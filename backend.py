#!/usr/bin/env python3
"""
Kartoshka Youtuber Backend
Console application for YouTube downloading
Created by NaderB - https://www.naderb.org
"""

import sys
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import yt_dlp
import argparse

# Windows consoles default to cp1252 — unicode titles/emojis crash print() and kill converts.
# Force UTF-8 for this process so JSON + filenames never blow up.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _safe_print(msg):
    """Never crash on unicode when writing to the console / GUI pipe."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((str(msg) + "\n").encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()
        except Exception:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"), flush=True)


def _safe_json(obj):
    _safe_print(json.dumps(obj, ensure_ascii=True))

def _get_ffmpeg_path():
    """Return path to ffmpeg.exe if found next to executable or script; else None (yt-dlp uses PATH)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    ffmpeg = os.path.join(base, 'ffmpeg.exe')
    return ffmpeg if os.path.isfile(ffmpeg) else None


def _ffmpeg_bin():
    """ffmpeg executable path or 'ffmpeg' from PATH."""
    return _get_ffmpeg_path() or 'ffmpeg'


def _fast_convert_to_mp3(input_path, output_path=None):
    """
    Convert any audio/video file to MP3 quickly (multi-threaded lame).
    Returns output path or raises on failure.
    """
    import subprocess

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")

    if not output_path:
        root, _ = os.path.splitext(input_path)
        output_path = root + '.mp3'

    # Avoid clobbering if somehow same path
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        output_path = os.path.splitext(input_path)[0] + '.converted.mp3'

    cmd = [
        _ffmpeg_bin(),
        '-hide_banner',
        '-loglevel', 'error',
        '-y',
        '-i', input_path,
        '-vn',                 # drop video — audio only
        '-map', '0:a:0',       # first audio stream
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        '-threads', '0',       # use all CPU cores
        '-id3v2_version', '3',
        output_path,
    ]
    _safe_print(f"Fast MP3 convert: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    _safe_json({'type': 'status', 'message': 'converting', 'file': os.path.basename(input_path)})
    sys.stdout.flush()

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or 'ffmpeg failed').strip()
        raise RuntimeError(err)

    # Remove source after successful convert (m4a/webm/opus leftovers)
    try:
        if os.path.abspath(input_path) != os.path.abspath(output_path) and os.path.isfile(output_path):
            os.remove(input_path)
    except OSError:
        pass

    return output_path


def _url_has_playlist(url):
    """True if URL points at a playlist / Mix / album list."""
    try:
        parsed = urlparse(url)
        path = (parsed.path or '').lower()
        if '/playlist' in path:
            return True
        qs = parse_qs(parsed.query)
        list_id = (qs.get('list') or [None])[0]
        return bool(list_id)
    except Exception:
        return 'list=' in (url or '')


def _playlist_id_from_url(url):
    try:
        qs = parse_qs(urlparse(url).query)
        return (qs.get('list') or [''])[0] or ''
    except Exception:
        return ''


def _is_mix_url(url):
    """YouTube Mix / radio queues use list IDs starting with RD."""
    return _playlist_id_from_url(url).startswith('RD')


# Mixes can resolve to hundreds of related videos; keep a sane default.
MIX_DEFAULT_LIMIT = 50
# YouTube rate-limits guest sessions (~300/hour). Pause between playlist items.
PLAYLIST_ITEM_PAUSE_SECONDS = 8

# When YouTube returns HTTP 403, retry with other InnerTube clients and/or
# browser cookies. Start with yt-dlp defaults — custom player_client lists
# must be valid (never use "default,-android_vr"; that disables all clients).
_ANTI_BLOCK_STRATEGIES = [
    {'name': 'yt-dlp-default'},
    {
        'name': 'web_safari+mweb+tv',
        'extractor_args': {'youtube': {'player_client': ['web_safari', 'mweb', 'tv']}},
    },
    {
        'name': 'tv+mweb+web',
        'extractor_args': {'youtube': {'player_client': ['tv', 'mweb', 'web']}},
    },
    {
        'name': 'chrome-cookies+web_safari',
        'cookiesfrombrowser': ('chrome',),
        'extractor_args': {'youtube': {'player_client': ['web_safari', 'mweb']}},
    },
    {
        'name': 'edge-cookies+web_safari',
        'cookiesfrombrowser': ('edge',),
        'extractor_args': {'youtube': {'player_client': ['web_safari', 'mweb']}},
    },
]


def _is_blocked_error(err):
    text = str(err).lower()
    return (
        '403' in text
        or 'forbidden' in text
        or 'sign in to confirm' in text
        or 'not a bot' in text
        or 'rate-limit' in text
        or 'rate limit' in text
    )


def _apply_anti_block_strategy(opts, strategy, cookies_browser=None):
    """Apply a yt-dlp strategy used by other tools to dodge YouTube CDN 403s."""
    if strategy.get('extractor_args'):
        opts['extractor_args'] = strategy['extractor_args']
    browser = cookies_browser or (strategy.get('cookiesfrombrowser') or (None,))[0]
    if browser:
        # (browser,) — yt-dlp fills profile automatically
        opts['cookiesfrombrowser'] = (browser,)
        _safe_print(f"Using cookies from browser: {browser}")
    elif 'cookiesfrombrowser' in opts:
        opts.pop('cookiesfrombrowser', None)


def _strip_playlist_from_url(url):
    """Keep only the single video (drop list / index / start_radio)."""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key in ('list', 'index', 'start_radio', 'pp'):
            qs.pop(key, None)
        # Rebuild query with first value per key
        flat = {k: v[0] for k, v in qs.items() if v}
        return urlunparse(parsed._replace(query=urlencode(flat)))
    except Exception:
        return url


def _extract_formats(info):
    """Build GUI-friendly format list from a video info dict."""
    formats = []
    for fmt in info.get('formats') or []:
        if fmt.get('vcodec') == 'none':
            continue
        resolution = fmt.get('resolution') or ''
        if not resolution:
            width = fmt.get('width')
            height = fmt.get('height')
            if width and height:
                resolution = f"{width}x{height}"
        formats.append({
            'format_id': fmt.get('format_id', ''),
            'ext': fmt.get('ext', ''),
            'resolution': resolution,
            'filesize': fmt.get('filesize') or fmt.get('filesize_approx', 0),
            'quality': fmt.get('height') or 0,
            'height': fmt.get('height') or 0,
            'width': fmt.get('width') or 0,
            'vcodec': fmt.get('vcodec', ''),
        })
    return formats


def _video_payload(info):
    return {
        'type': 'video',
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration', 0) or 0,
        'uploader': info.get('uploader', 'Unknown'),
        'view_count': info.get('view_count', 0) or 0,
        'thumbnail': info.get('thumbnail', ''),
        'formats': _extract_formats(info),
        'is_playlist': False,
        'entry_count': 1,
    }


class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            # Default to best available video+audio, GUI can still request specific qualities
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': False,
        }
        self.download_path = str(Path.home() / "Downloads")
        
    def set_download_path(self, path):
        """Set the download directory"""
        self.download_path = path
        os.makedirs(path, exist_ok=True)
        
    def ensure_download_path(self):
        """Ensure download path exists"""
        os.makedirs(self.download_path, exist_ok=True)

    def get_video_info(self, url):
        """Get video or playlist information without downloading."""
        try:
            # Flat extract is fast for playlists / Mixes; formats come from the first entry.
            opts = {
                'quiet': True,
                'extract_flat': True,
                'noplaylist': False,
                'ignoreerrors': True,
            }
            is_mix = _is_mix_url(url)
            if is_mix:
                opts['playlistend'] = MIX_DEFAULT_LIMIT

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return {'error': 'Could not extract info from URL'}

            # Playlist / Mix / album
            if info.get('_type') == 'playlist' or info.get('entries') is not None:
                entries_raw = list(info.get('entries') or [])
                entries = []
                first_full = None
                for i, entry in enumerate(entries_raw):
                    if not entry:
                        continue
                    video_id = entry.get('id') or ''
                    title = entry.get('title') or 'Unknown'
                    duration = entry.get('duration') or 0
                    webpage = entry.get('webpage_url') or entry.get('url') or ''
                    if video_id and not str(webpage).startswith('http'):
                        webpage = f"https://www.youtube.com/watch?v={video_id}"
                    elif not video_id and str(webpage).startswith('http'):
                        # flat url may be the watch URL or just an id
                        video_id = webpage
                    entries.append({
                        'index': i + 1,
                        'id': video_id,
                        'title': title,
                        'duration': duration,
                        'url': webpage if str(webpage).startswith('http') else f"https://www.youtube.com/watch?v={video_id}",
                    })
                    # Resolve formats from first real entry (flat entries lack formats)
                    if first_full is None and (video_id or webpage):
                        probe_url = webpage if str(webpage).startswith('http') else f"https://www.youtube.com/watch?v={video_id}"
                        try:
                            with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl2:
                                first_full = ydl2.extract_info(probe_url, download=False)
                        except Exception as probe_err:
                            _safe_print(f"Could not probe first playlist entry formats: {probe_err}")

                playlist_title = info.get('title') or info.get('id') or 'Playlist'
                list_id = info.get('id') or _playlist_id_from_url(url)
                is_mix = is_mix or str(list_id).startswith('RD')

                result = {
                    'type': 'playlist',
                    'is_playlist': True,
                    'is_mix': is_mix,
                    'playlist_limit': MIX_DEFAULT_LIMIT if is_mix else None,
                    'playlist_title': playlist_title,
                    'playlist_id': list_id,
                    'uploader': info.get('uploader') or info.get('channel') or 'Unknown',
                    'entry_count': len(entries),
                    'entries': entries,
                    'title': playlist_title,
                    'duration': sum((e.get('duration') or 0) for e in entries),
                    'view_count': 0,
                    'thumbnail': (first_full or {}).get('thumbnail', '') or info.get('thumbnail', ''),
                    'formats': _extract_formats(first_full) if first_full else [],
                }
                if first_full:
                    result['preview_title'] = first_full.get('title', '')
                return result

            return _video_payload(info)
        except Exception as e:
            return {'error': str(e)}
    
    def download_video(self, url, quality='best', output_format='mp4', no_playlist=False, filename_prefix='', no_convert=False, cookies_from_browser=None):
        """Download a single video or an entire playlist / Mix."""
        try:
            self.ensure_download_path()

            if no_playlist and _url_has_playlist(url):
                url = _strip_playlist_from_url(url)
                _safe_print(f"Single-video mode; using URL: {url}")

            download_playlist = (not no_playlist) and _url_has_playlist(url)
            is_mix = download_playlist and _is_mix_url(url)
            _safe_print(f"Downloading with quality: {quality}, format: {output_format}, playlist={download_playlist}, mix={is_mix}, no_convert={no_convert}")

            base_opts = self.ydl_opts.copy()
            base_opts['noplaylist'] = bool(no_playlist)
            base_opts['retries'] = 5
            base_opts['fragment_retries'] = 5
            base_opts['concurrent_fragment_downloads'] = 1
            base_opts['ignoreerrors'] = bool(download_playlist)
            # Small polite delay on every request — reduces bot / rate-limit 403s
            base_opts['sleep_interval_requests'] = 1
            # ASCII-safe names — unicode titles crash Windows cp1252 pipes / convert
            base_opts['restrictfilenames'] = True
            base_opts['windowsfilenames'] = True
            base_opts['sleep_interval'] = 1
            base_opts['max_sleep_interval'] = 3
            if is_mix:
                base_opts['playlistend'] = MIX_DEFAULT_LIMIT
                _safe_print(f"Mix download limited to first {MIX_DEFAULT_LIMIT} items")

            prefix = filename_prefix or ''
            if download_playlist:
                base_opts['outtmpl'] = os.path.join(
                    self.download_path,
                    '%(playlist_title|playlist)s',
                    '%(playlist_index)03d - %(title)s.%(ext)s',
                )
                base_opts['sleep_interval'] = PLAYLIST_ITEM_PAUSE_SECONDS
                base_opts['max_sleep_interval'] = PLAYLIST_ITEM_PAUSE_SECONDS
                _safe_print(f"Playlist mode: one-by-one with ~{PLAYLIST_ITEM_PAUSE_SECONDS}s pause between items")
            else:
                base_opts['outtmpl'] = os.path.join(self.download_path, f'{prefix}%(title)s.%(ext)s')

            height = None
            if quality not in ('best', 'worst') and quality:
                height = quality.split('x')[1] if 'x' in quality else quality

            if output_format == 'mp3':
                # Prefer m4a — format 251 (webm/opus via android_vr) often 403s on CDN
                base_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[acodec*=mp4a]/bestaudio/best'
                base_opts['postprocessors'] = []
            else:
                if quality == 'best':
                    base_opts['format'] = 'bestvideo[height<=4320]+bestaudio/best'
                elif quality == 'worst':
                    base_opts['format'] = f'worst[ext={output_format}]/worst'
                elif height:
                    base_opts['format'] = (
                        f'bestvideo[height<={height}]+bestaudio/'
                        f'best[height<={height}]/'
                        f'bestvideo+bestaudio/best'
                    )
                    _safe_print(f"Using format selector for height <= {height}")
                else:
                    base_opts['format'] = 'bestvideo+bestaudio/best'

                if output_format == 'mp4':
                    base_opts['merge_output_format'] = 'mp4'
                    base_opts['postprocessors'] = []
                elif output_format in ['webm', 'mkv']:
                    base_opts['merge_output_format'] = output_format
                    base_opts['postprocessors'] = []

            ffmpeg_path = _get_ffmpeg_path()
            if ffmpeg_path:
                base_opts['ffmpeg_location'] = ffmpeg_path

            strategies = list(_ANTI_BLOCK_STRATEGIES)
            # Optional browser cookies — last resort only (Chrome must be closed).
            if cookies_from_browser:
                strategies.append({
                    'name': f'browser-{cookies_from_browser}',
                    'cookiesfrombrowser': (cookies_from_browser,),
                    'extractor_args': {'youtube': {'player_client': ['web_safari', 'mweb']}},
                })

            downloaded_file = {'path': None}
            playlist_state = {'index': 0, 'count': 0, 'title': ''}
            last_error = None

            def progress_hook(d):
                status = d.get('status')
                info_dict = d.get('info_dict') or {}
                if info_dict.get('playlist_index'):
                    playlist_state['index'] = info_dict.get('playlist_index') or 0
                    playlist_state['count'] = info_dict.get('n_entries') or playlist_state['count']
                    playlist_state['title'] = info_dict.get('playlist_title') or playlist_state['title']

                if status == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        speed = d.get('speed', 0)
                        eta = d.get('eta', 0)
                        pfx = ''
                        if download_playlist and playlist_state['index']:
                            pfx = f"[{playlist_state['index']}/{playlist_state['count'] or '?'}] "
                        _safe_print(f"{pfx}Progress: {percent:.1f}% - Speed: {speed} - ETA: {eta}")
                        _safe_json({
                            'type': 'progress',
                            'percent': percent,
                            'speed': speed,
                            'eta': eta,
                            'playlist_index': playlist_state['index'],
                            'playlist_count': playlist_state['count'],
                        })
                        sys.stdout.flush()
                elif status == 'finished':
                    filename = d.get('filename')
                    if filename:
                        downloaded_file['path'] = filename
                    if download_playlist and playlist_state['index']:
                        _safe_print(f"Finished item {playlist_state['index']}/{playlist_state['count'] or '?'}")
                    else:
                        _safe_print("Download finished successfully")

            for attempt, strategy in enumerate(strategies):
                ydl_opts = base_opts.copy()
                ydl_opts['progress_hooks'] = [progress_hook]
                downloaded_file['path'] = None
                _apply_anti_block_strategy(ydl_opts, strategy, cookies_browser=None)
                _safe_print(f"Anti-block strategy [{attempt + 1}/{len(strategies)}]: {strategy['name']}")

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        if info:
                            for rd in info.get('requested_downloads') or []:
                                fp = rd.get('filepath')
                                if fp and os.path.isfile(fp):
                                    downloaded_file['path'] = fp
                                    break
                            if not downloaded_file['path']:
                                try:
                                    candidate = ydl.prepare_filename(info)
                                    if candidate and os.path.isfile(candidate):
                                        downloaded_file['path'] = candidate
                                    else:
                                        root, _ = os.path.splitext(candidate or '')
                                        for ext in ('.m4a', '.webm', '.opus', '.ogg', '.mp3', '.mp4', '.mkv'):
                                            alt = root + ext
                                            if os.path.isfile(alt):
                                                downloaded_file['path'] = alt
                                                break
                                except Exception:
                                    pass
                        _safe_print("Download completed successfully")
                    last_error = None
                    break
                except Exception as download_error:
                    last_error = download_error
                    _safe_print(f"Download error ({strategy['name']}): {download_error}")
                    self.cleanup_partial_files()
                    if attempt < len(strategies) - 1:
                        err_text = str(download_error).lower()
                        if 'cookie' in err_text or 'no player clients' in err_text:
                            wait = 1
                        elif _is_blocked_error(download_error):
                            wait = 5 + attempt * 3
                        else:
                            wait = 2
                        _safe_print(f"Strategy failed. Waiting {wait}s, then trying another method...")
                        _safe_json({'type': 'status', 'message': 'retry_403', 'wait': wait, 'strategy': strategy['name']})
                        sys.stdout.flush()
                        time.sleep(wait)
                        continue
                    # Non-retryable or last strategy — give up
                    raise download_error

            if last_error:
                raise last_error

            final_path = downloaded_file['path']

            if output_format == 'mp3' and not no_convert and final_path and os.path.isfile(final_path):
                if not final_path.lower().endswith('.mp3'):
                    final_path = _fast_convert_to_mp3(final_path)

            if download_playlist:
                msg = f'Playlist download completed successfully as {output_format}'
            else:
                msg = f'Download completed successfully as {output_format}'
            return {
                'success': True,
                'message': msg,
                'is_playlist': download_playlist,
                'filepath': final_path,
                'needs_convert': bool(output_format == 'mp3' and no_convert),
            }

        except Exception as e:
            _safe_print(f"Download failed: {e}")
            self.cleanup_partial_files()
            tip = ''
            if _is_blocked_error(e):
                tip = (
                    ' YouTube is blocking this IP/session (common on Mix/playlist bulk downloads). '
                    'Wait a few minutes and try again. Close Chrome/Edge and retry for cookie-based fallback.'
                )
            return {'success': False, 'error': str(e) + tip}

    def convert_file(self, input_path, output_format='mp3'):
        """Convert a downloaded file (used so GUI can convert while next song downloads)."""
        try:
            if not input_path or not os.path.isfile(input_path):
                return {'success': False, 'error': f'Input file not found: {input_path}'}
            if output_format != 'mp3':
                return {'success': False, 'error': f'Unsupported convert format: {output_format}'}
            out = _fast_convert_to_mp3(input_path)
            return {'success': True, 'message': 'Converted to MP3', 'filepath': out}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cleanup_partial_files(self):
        """Clean up partial download files (including nested playlist folders)."""
        try:
            for root, _dirs, files in os.walk(self.download_path):
                for file in files:
                    if file.endswith('.part'):
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        print(f"Removed partial file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up partial files: {e}")

def main():
    """Main console application"""
    parser = argparse.ArgumentParser(description='Kartoshka Youtuber Backend')
    parser.add_argument('--command', required=True, help='Command to execute')
    parser.add_argument('--url', help='YouTube URL')
    parser.add_argument('--quality', default='best', help='Video quality')
    parser.add_argument('--format', default='mp4', help='Output format')
    parser.add_argument('--path', help='Download path')
    parser.add_argument(
        '--no-playlist',
        action='store_true',
        help='Download only the current video even if URL contains list=',
    )
    parser.add_argument(
        '--filename-prefix',
        default='',
        help='Optional filename prefix (e.g. "001 - ") for single-video downloads',
    )
    parser.add_argument(
        '--no-convert',
        action='store_true',
        help='For mp3: download audio only and skip convert (GUI converts in parallel)',
    )
    parser.add_argument('--input', help='Input file path for convert command')
    parser.add_argument(
        '--cookies-from-browser',
        default='',
        help='Browser name for cookies (chrome, edge, firefox) — helps avoid YouTube 403',
    )
    
    args = parser.parse_args()
    
    downloader = YouTubeDownloader()
    
    if args.path:
        downloader.set_download_path(args.path)
    
    if args.command == 'info':
        if not args.url:
            _safe_json({'error': 'URL is required for info command'})
            sys.exit(1)
            
        info = downloader.get_video_info(args.url)
        _safe_json(info)
        
    elif args.command == 'download':
        if not args.url:
            _safe_json({'error': 'URL is required for download command'})
            sys.exit(1)
        
        result = downloader.download_video(
            args.url,
            args.quality,
            args.format,
            no_playlist=args.no_playlist,
            filename_prefix=args.filename_prefix or '',
            no_convert=args.no_convert,
            cookies_from_browser=(args.cookies_from_browser or '').strip() or None,
        )
        _safe_json(result)

    elif args.command == 'convert':
        if not args.input:
            _safe_json({'error': 'Input file is required for convert command'})
            sys.exit(1)
        result = downloader.convert_file(args.input, args.format or 'mp3')
        _safe_json(result)
        
    else:
        _safe_json({'error': f'Unknown command: {args.command}'})
        sys.exit(1)

if __name__ == '__main__':
    main()



