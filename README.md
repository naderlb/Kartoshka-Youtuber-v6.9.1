# Kartoshka Youtuber v6.9.1

A clean, modern YouTube downloader with a beautiful GUI interface.

**Created by NaderB - https://www.naderb.org**

## Features

- **Modern GUI Interface** - Clean, intuitive design
- **Fast Downloads** - Optimized for speed and reliability  
- **Multiple Qualities** - Best, 720p, 480p, 360p, and more
- **Format Support** - MP4, WebM, MKV, Audio-only
- **Real-time Progress** - Live download progress with speed and ETA
- **Video Information** - Preview title, duration, uploader, views
- **Playlist Support** - Download entire playlists with selective video choice
- **Customizable Settings** - Save your preferences
- **Standalone Executables** - No Python installation required

## Architecture

This application uses a **two-part architecture** for maximum reliability:

1. **Backend Console App** (`kartoshka-backend.exe`) - Handles all YouTube downloading
2. **GUI Frontend** (`kartoshka-youtuber.exe`) - Beautiful interface that communicates with backend

## Quick Start

### Option 1: Use Pre-built Executables (Recommended)

1. Download the `release` folder
2. Run `kartoshka-youtuber.exe`
3. Enter a YouTube URL and start downloading!

### Option 2: Build from Source

1. **Install Python 3.8+** (if not already installed)
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Test the application:**
   ```bash
   python test_app.py
   ```
4. **Build executables:**
   ```bash
   python build.py
   ```
   Or simply run: `build.bat`

## How to Use

1. **Launch the application** by running `kartoshka-youtuber.exe`
2. **Enter a YouTube URL** in the URL field
3. **Click "Get Info"** to preview video details
4. **Select quality and format** from the dropdowns
5. **Choose download location** (defaults to Downloads folder)
6. **Click "Download"** to start downloading
7. **Monitor progress** in real-time with speed and ETA

## Supported URLs

- Single videos: `https://www.youtube.com/watch?v=VIDEO_ID`
- Short URLs: `https://youtu.be/VIDEO_ID`
- Playlists: `https://www.youtube.com/playlist?list=PLAYLIST_ID`
- Channels: `https://www.youtube.com/channel/CHANNEL_ID`

## Quality Options

- **Best** - Highest available quality
- **Worst** - Lowest available quality  
- **720p** - HD quality (1280x720)
- **480p** - Standard quality (854x480)
- **360p** - Lower quality (640x360)

## Format Options

- **MP4** - Most compatible video format
- **WebM** - Modern web format
- **MKV** - High-quality container
- **Audio** - Audio-only download

## Troubleshooting

### "Backend application not found"
- Make sure both `kartoshka-youtuber.exe` and `kartoshka-backend.exe` are in the same folder
- Try running `kartoshka-backend.exe` directly to test

### "Download failed" errors
- Check your internet connection
- Verify the YouTube URL is valid
- Try a different quality or format
- Some videos may be region-restricted

### GUI not starting
- Make sure you're on Windows 7 or later
- Try running as administrator
- Check Windows Defender isn't blocking the application

## Technical Details

- **Backend**: Python with yt-dlp library
- **Frontend**: Python with tkinter GUI
- **Packaging**: PyInstaller for standalone executables
- **Communication**: JSON over subprocess calls
- **Platform**: Windows (can be adapted for other platforms)

## Libraries Used

This project is built using the following open-source libraries and tools:

### Core Libraries
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The most powerful YouTube downloader library
- **[PyInstaller](https://github.com/pyinstaller/pyinstaller)** - Converts Python applications into standalone executables
- **[FFmpeg](https://ffmpeg.org/)** - Complete multimedia framework for audio/video processing
- **[ffmpeg-python](https://github.com/kkroening/ffmpeg-python)** - Python bindings for FFmpeg
- **[mutagen](https://github.com/quodlibet/mutagen)** - Python audio metadata library

### Built-in Libraries
- **tkinter** - Python's standard GUI toolkit
- **subprocess** - Process management and communication
- **json** - Data serialization
- **threading** - Asynchronous operations
- **os/sys** - System operations and path handling

## Credits and Acknowledgments

This project would not be possible without the incredible work of the open-source community:

### Primary Dependencies
- **yt-dlp Team** - For creating the most reliable YouTube downloader. This project is a fork of youtube-dl with continuous improvements and bug fixes.
- **PyInstaller Team** - For making it possible to distribute Python applications as standalone executables.
- **FFmpeg Team** - For providing the industry-standard multimedia processing framework that handles all audio/video conversion.

### Special Thanks
- **Python Software Foundation** - For the amazing Python programming language and its extensive standard library
- **Tkinter/Tk** - For providing a robust GUI framework that works across platforms
- **Open Source Community** - For the countless hours of development, testing, and documentation that make projects like this possible

### Inspiration
This project was inspired by the need for a clean, user-friendly YouTube downloader that doesn't require technical knowledge to use. We believe in making technology accessible to everyone.

**Note**: This application is for educational purposes. Please respect YouTube's Terms of Service and only download content you own or have permission to download.

## File Structure

```
kartoshka-youtuber/
├── backend.py              # Console backend application
├── gui.py                  # GUI frontend application  
├── build.py                # Build script
├── test_app.py             # Test script
├── requirements.txt        # Python dependencies
├── build.bat              # Windows build script
├── icon.ico               # Application icon
└── release/               # Built executables
    ├── kartoshka-youtuber.exe
    ├── kartoshka-backend.exe
    └── README.txt
```

## Development

To modify or extend the application:

1. **Edit the backend** (`backend.py`) for download logic
2. **Edit the GUI** (`gui.py`) for interface changes
3. **Test changes** with `python test_app.py`
4. **Rebuild** with `python build.py`

## License

This project is created by NaderB. Feel free to use and modify for personal use.

## Version History

### v6.9.1
- Added playlist detection and selection interface
- Selective playlist download with checkboxes
- Individual video selection from playlists
- Enhanced playlist management
- Improved user experience for large playlists

### v6.9
- Complete rewrite with two-part architecture
- Modern GUI with real-time progress
- Standalone executables
- Better error handling
- Basic playlist support

---

**Created by NaderB**

Visit https://www.naderb.org for more projects!



