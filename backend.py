#!/usr/bin/env python3
"""
Kartoshka Youtuber Backend
Console application for YouTube downloading
Created by NaderB - https://www.naderb.org
"""

import sys
import json
import subprocess
import os
import threading
import time
from pathlib import Path
import yt_dlp
import argparse

def _get_ffmpeg_path():
    """Return path to ffmpeg.exe if found next to executable or script; else None (yt-dlp uses PATH)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    ffmpeg = os.path.join(base, 'ffmpeg.exe')
    return ffmpeg if os.path.isfile(ffmpeg) else None


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
        """Get video information without downloading (full list of formats)."""
        try:
            # Let yt-dlp pick the best extractor/client combination; this usually exposes all qualities
            opts = {'quiet': True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            video_info = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': []
            }

            for fmt in info.get('formats', []):
                # Only keep video formats (GUI uses these to build quality buttons)
                if fmt.get('vcodec') == 'none':
                    continue

                # Some formats don't have a human-readable resolution string, so build one from width/height
                resolution = fmt.get('resolution') or ''
                if not resolution:
                    width = fmt.get('width')
                    height = fmt.get('height')
                    if width and height:
                        resolution = f"{width}x{height}"

                video_info['formats'].append({
                    'format_id': fmt.get('format_id', ''),
                    'ext': fmt.get('ext', ''),
                    'resolution': resolution,
                    'filesize': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                    'quality': fmt.get('height') or 0,
                })

            return video_info
        except Exception as e:
            return {'error': str(e)}
    
    def download_video(self, url, quality='best', output_format='mp4'):
        """Download video with progress tracking"""
        try:
            # Ensure download path exists
            self.ensure_download_path()
            
            # Debug: Print the quality being used
            print(f"Downloading with quality: {quality}, format: {output_format}")
            
            # Configure download options
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(title)s.%(ext)s')
            
            # Add better error handling and retry options
            ydl_opts['retries'] = 3
            ydl_opts['fragment_retries'] = 3
            ydl_opts['ignoreerrors'] = False
            
            # Handle audio-only downloads
            if output_format == 'mp3':
                # Use yt-dlp's built-in MP3 conversion with local FFmpeg
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                # Force MP3 extension
                ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(title)s.%(ext)s')
                # Add strong FFmpeg options to force MP3 conversion
                ydl_opts['postprocessor_args'] = {
                    'FFmpegExtractAudio': [
                        '-acodec', 'libmp3lame',
                        '-ab', '192k',
                        '-ar', '44100',
                        '-ac', '2',
                        '-f', 'mp3'
                    ]
                }
                ffmpeg_path = _get_ffmpeg_path()
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path
            else:
                # Set format based on quality preference for video
                if quality == 'best':
                    # Allow up to 4K+ and merge best video+audio; container is normalized by postprocessor
                    ydl_opts['format'] = 'bestvideo[height<=4320]+bestaudio/best'
                elif quality == 'worst':
                    ydl_opts['format'] = f'worst[ext={output_format}]/worst'
                else:
                    # Try to get specific quality in requested format, fallback to best available
                    # Extract height from quality string (e.g., "1920x1080" -> "1080")
                    if 'x' in quality:
                        height = quality.split('x')[1]  # Get the height part (second number)
                    else:
                        height = quality
                    
                    print(f"Looking for video with height: {height}, format: {output_format}")

                    # First, get available formats to find the best match (let yt-dlp choose the best extractor)
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                        available_formats = info.get('formats', [])
                        
                        # Find the best format matching our criteria
                        best_format = None
                        
                        # First try: exact height + exact format
                        for fmt in available_formats:
                            if (fmt.get('vcodec') != 'none' and 
                                fmt.get('height') and 
                                int(fmt.get('height', 0)) == int(height) and
                                fmt.get('ext') == output_format):
                                best_format = fmt
                                break
                        
                        # Second try: exact height + any format
                        if not best_format:
                            for fmt in available_formats:
                                if (fmt.get('vcodec') != 'none' and 
                                    fmt.get('height') and 
                                    int(fmt.get('height', 0)) == int(height)):
                                    best_format = fmt
                                    break
                        
                        # Third try: higher height + exact format
                        if not best_format:
                            for fmt in available_formats:
                                if (fmt.get('vcodec') != 'none' and 
                                    fmt.get('height') and 
                                    int(fmt.get('height', 0)) >= int(height) and
                                    fmt.get('ext') == output_format):
                                    best_format = fmt
                                    break
                        
                        # Fourth try: higher height + any format
                        if not best_format:
                            for fmt in available_formats:
                                if (fmt.get('vcodec') != 'none' and 
                                    fmt.get('height') and 
                                    int(fmt.get('height', 0)) >= int(height)):
                                    best_format = fmt
                                    break
                        
                        if best_format:
                            format_id = best_format.get('format_id')
                            print(f"Selected format: {format_id} - {best_format.get('height')}p {best_format.get('ext')}")
                            
                            # For video downloads, we need to merge video + audio
                            # Check if this format has audio, if not, add best audio
                            if best_format.get('acodec') == 'none':
                                # Video-only format, need to add audio
                                audio_format = None
                                for fmt in available_formats:
                                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                                        audio_format = fmt.get('format_id')
                                        break
                                
                                if audio_format:
                                    ydl_opts['format'] = f'{format_id}+{audio_format}'
                                    print(f"Adding audio format: {audio_format}")
                                else:
                                    ydl_opts['format'] = format_id
                                    print("Warning: No audio format found, video will be silent")
                            else:
                                ydl_opts['format'] = format_id
                        else:
                            print(f"No suitable format found, using fallback")
                            ydl_opts['format'] = f'best[height<={height}][ext={output_format}]/best[height<={height}]/best'
                
                # Force the output extension
                ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(title)s.%(ext)s')
                
                # Add post-processor for video format conversion if needed
                if output_format in ['mp4', 'webm', 'mkv']:
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': output_format,
                    }]
                
                ffmpeg_path = _get_ffmpeg_path()
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path

            # Progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        speed = d.get('speed', 0)
                        eta = d.get('eta', 0)
                        # Print progress to console for debugging
                        print(f"Progress: {percent:.1f}% - Speed: {speed} - ETA: {eta}")
                elif d['status'] == 'finished':
                    print("Download finished successfully")
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # First, get info about available formats for debugging
                    info = ydl.extract_info(url, download=False)
                    if 'formats' in info:
                        print("Available formats:")
                        for fmt in info['formats']:
                            if fmt.get('vcodec') != 'none':  # Video formats
                                print(f"  {fmt.get('format_id')}: {fmt.get('height')}p {fmt.get('ext')} {fmt.get('vcodec')}")
                    
                    ydl.download([url])
                    print("Download completed successfully")
                except Exception as download_error:
                    print(f"Download error: {download_error}")
                    # Clean up any partial files
                    self.cleanup_partial_files()
                    raise download_error
                
            return {'success': True, 'message': f'Download completed successfully as {output_format}'}
            
        except Exception as e:
            print(f"Download failed: {e}")
            # Clean up any partial files
            self.cleanup_partial_files()
            return {'success': False, 'error': str(e)}
    
    def cleanup_partial_files(self):
        """Clean up partial download files"""
        try:
            for file in os.listdir(self.download_path):
                if file.endswith('.part'):
                    file_path = os.path.join(self.download_path, file)
                    os.remove(file_path)
                    print(f"Removed partial file: {file}")
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
    
    args = parser.parse_args()
    
    downloader = YouTubeDownloader()
    
    if args.path:
        downloader.set_download_path(args.path)
    
    if args.command == 'info':
        # Get video information
        if not args.url:
            print(json.dumps({'error': 'URL is required for info command'}))
            sys.exit(1)
            
        info = downloader.get_video_info(args.url)
        print(json.dumps(info))
        
    elif args.command == 'download':
        # Download video
        if not args.url:
            print(json.dumps({'error': 'URL is required for download command'}))
            sys.exit(1)
            
        def progress_callback(percent, speed, eta):
            progress_data = {
                'type': 'progress',
                'percent': percent,
                'speed': speed,
                'eta': eta
            }
            print(json.dumps(progress_data))
            sys.stdout.flush()
        
        result = downloader.download_video(
            args.url, 
            args.quality, 
            args.format
        )
        print(json.dumps(result))
        
    else:
        print(json.dumps({'error': f'Unknown command: {args.command}'}))
        sys.exit(1)

if __name__ == '__main__':
    main()



