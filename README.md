# 🔥 Kartoshka Youtuber v6.9

A clean, modern YouTube downloader with an easy to use GUI interface.

![Screenshot](docs/app.png)


**Created by NaderB - https://www.naderb.org**  
**Last updated: 2026-04-29**

📦 **Download:** [Get the complete package (GUI + backend) at naderb.org/kartoshka.php](https://naderb.org/kartoshka)

## Features

- **Modern GUI Interface** - Clean, intuitive design
- **Fast Downloads** - Optimized for speed and reliability  
- **Multiple Qualities** - Best,4k, 1080p 720p, 480p, 360p, and more
- **Format Support** - MP4, WebM, MKV, Audio-only
- **Real-time Progress** - Live download progress with speed and ETA
- **Video Information** - Preview title, duration, uploader, views
- **Customizable Settings** - Save your preferences
- **Standalone Executables** - No Python installation required

## Architecture

This application uses a **two-part architecture** for maximum reliability:

1. **Backend Console App** (`kartoshka-backend.exe`) - Handles all YouTube downloading
2. **GUI Frontend** (`kartoshka-youtuber.exe`) - Beautiful interface that communicates with backend

## Quick Start

### Option 1: Use Pre-built Executables (Recommended)

1. **Download the package:** [naderb.org/kartoshka.php](https://naderb.org/kartoshka) (includes GUI, backend, ffmpeg, and instructions)
2. Extract the zip and run `kartoshka-youtuber.exe`
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

## Quality Options
- **Best** – Download the highest video quality available
- **Worst** – Download the lowest available quality for smaller file size
- **720p** – HD video quality (1280 × 720)
- **480p** – Standard video quality (854 × 480)
- **360p** – Lower quality for faster downloads and reduced file size (640 × 360)
- **Full HD** – Supports 1080p and any higher quality available

## Format Options

- **MP4** - Most compatible video format
- **WebM** - Modern web format
- **MKV** - High-quality container
- **Audio** - Audio-only download

## Troubleshooting

### "Backend application not found"
- Make sure both `kartoshka-youtuber.exe` and `kartoshka-backend.exe` are in the same folder
- Try running `kartoshka-backend.exe` directly to test

### "Download failed" or "Get Info" errors / YouTube "unavailable"
- **Update yt-dlp** — YouTube changes their API often; keep the library current:
  ```bash
  pip install -U yt-dlp
  ```
  Then rebuild with `python build.py` if you use the executables.
- Check your internet connection
- Verify the YouTube URL is valid
- Try a different quality or format
- Some videos may be region-restricted

### GUI not starting
- Make sure you're on Windows 7 or later
- Try running as administrator
- Check Windows Defender isn't blocking the application

## Technical Details

- **Backend**: Python 3.x with yt-dlp (e.g. 2026.x)
- **Frontend**: C# WPF desktop app — **.NET 8**, Windows-only, self-contained single-file exe
- **GUI project**: `KartoshkaYoutuber.csproj` (WPF, `net8.0-windows`)
- **Packaging**: PyInstaller for backend; `dotnet publish -r win-x64 --self-contained` for GUI
- **Communication**: JSON over subprocess (GUI launches backend exe or `python backend.py`)
- **Platform**: Windows (x64)

### C# / GUI stack

| Item        | Value                          |
|------------|---------------------------------|
| Framework  | .NET 8                          |
| UI         | WPF (Windows Presentation Foundation) |
| Target     | `net8.0-windows`                |
| Publish    | Self-contained, single-file exe (no .NET install required on target PC) |
| Build      | `dotnet publish -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true` |

## Libraries Used

This project is built using the following open-source libraries and tools:

### Core Libraries
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The most powerful YouTube downloader library
- **[PyInstaller](https://github.com/pyinstaller/pyinstaller)** - Converts Python applications into standalone executables
- **[FFmpeg](https://ffmpeg.org/)** - Complete multimedia framework for audio/video processing
- **[ffmpeg-python](https://github.com/kkroening/ffmpeg-python)** - Python bindings for FFmpeg
- **[mutagen](https://github.com/quodlibet/mutagen)** - Python audio metadata library

### Built-in Libraries
- **subprocess** (Python) - Process management and communication
- **json** (Python) - Data serialization
- **threading** (Python) - Asynchronous operations
- **os/sys** (Python) - System operations and path handling
- **.NET / WPF** (C#) - Modern Windows desktop UI

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

## Development

To modify or extend the application:

1. **Edit the backend** (`backend.py`) for download logic
2. **Edit the GUI** (C# WPF: `MainWindow.xaml` / `MainWindow.xaml.cs`)
3. **Test backend** with `python test_app.py`
4. **Rebuild backend** with `python build.py`
5. **Build GUI** with `dotnet build` (or `dotnet publish`) in the project folder

## License
MIT License

Copyright (c) 2026 Nader Barakat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## Version History

### 2026-03-15 (C# GUI)
- GUI rewritten in **C# WPF** (.NET 8); Python Tkinter GUI removed
- Self-contained `kartoshka-youtuber.exe` (no .NET required on user machines)
- Backend remains Python/yt-dlp; yt-dlp pinned to 2026.x
- Format combo and UI readability fixes

### v6.9
- Complete rewrite with two-part architecture
- Modern GUI with real-time progress
- Standalone executables
- Better error handling

---

**Created by NaderB**

- **Download:** [Kartoshka YouTube Downloader (naderb.org/kartoshka.php)](https://naderb.org/kartoshka)  
- **More projects:** https://www.naderb.org



