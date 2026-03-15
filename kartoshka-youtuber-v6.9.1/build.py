#!/usr/bin/env python3
"""
Build script for Kartoshka Youtuber
Creates standalone executables for Windows
Created by NaderB - https://www.naderb.org
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    """Print build header"""
    print("=" * 50)
    print("Building Kartoshka Youtuber v6.9.1")
    print("=" * 50)
    print("Created by NaderB - https://www.naderb.org")
    print("A professional YouTube downloader")
    print("=" * 50)
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    # Install all requirements from requirements.txt
    if os.path.exists("requirements.txt"):
        print("Installing requirements from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("All requirements installed")
    else:
        # Fallback to individual package installation
        packages = ["yt-dlp", "pyinstaller", "ffmpeg-python"]
        for package in packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"{package} found")
            except ImportError:
                print(f"{package} not found. Installing...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"{package} installed")
    
    print()

def build_backend():
    """Build the backend executable"""
    print("Building backend executable...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console",
        "--name", "kartoshka-backend",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--hidden-import", "ffmpeg",
        "--hidden-import", "yt_dlp",
        "backend.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Backend built successfully")
    except subprocess.CalledProcessError as e:
        print(f"Backend build failed: {e}")
        return False
    
    return True

def build_gui():
    """Build the GUI executable"""
    print("Building GUI executable...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "kartoshka-youtuber",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--hidden-import", "ffmpeg",
        "--hidden-import", "yt_dlp",
        "gui.py"
    ]
    
    # Add icon if it exists
    icon_path = os.path.abspath("icon.ico")
    if os.path.exists(icon_path):
        cmd.extend(["--add-data", f"{icon_path};."])
        cmd.extend(["--icon", icon_path])
    else:
        icon_path = os.path.abspath("icon.png")
        if os.path.exists(icon_path):
            cmd.extend(["--add-data", f"{icon_path};."])
            cmd.extend(["--icon", icon_path])
    
    try:
        subprocess.run(cmd, check=True)
        print("GUI built successfully")
    except subprocess.CalledProcessError as e:
        print(f"GUI build failed: {e}")
        return False
    
    return True

def create_release_package():
    """Create the final release package"""
    print("Creating release package...")
    
    # Create release directory
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    # Copy executables
    shutil.copy2("dist/kartoshka-youtuber.exe", "release/")
    shutil.copy2("dist/kartoshka-backend.exe", "release/")
    
    # Copy icon if exists
    if os.path.exists("icon.ico"):
        shutil.copy2("icon.ico", "release/")
    elif os.path.exists("icon.png"):
        shutil.copy2("icon.png", "release/")
    
    # Create README
    readme_content = """# Kartoshka Youtuber v6.9.1

A professional YouTube downloader with modern GUI interface.

## How to Use

1. Run `kartoshka-youtuber.exe` to start the GUI
2. Enter a YouTube URL (single video or playlist)
3. Click "Get Info" to see video details and available qualities
4. For playlists: Select which videos to download using checkboxes
5. Select quality and format (including MP3 audio)
6. Click "Download" to start downloading

## Files

- `kartoshka-youtuber.exe` - Main GUI application
- `kartoshka-backend.exe` - Backend downloader (required)
- `icon.ico` - Application icon

## Requirements

- Windows 7 or later
- No additional software installation required
- Downloads are saved to the 'download' folder

## Features

- Professional GUI interface with quality selection
- Real-time progress tracking
- Multiple quality options with visual selection
- Playlist support with selective video download
- MP3 audio download support
- Silent operation (no console popups)
- Automatic download folder creation
- Individual video selection from playlists

## Important Notice

This software is for educational and personal use only. You should only download content that you own or have explicit permission to download. Respect copyright laws and YouTube's Terms of Service. The developers are not responsible for any misuse of this software.

## Created by NaderB

Visit https://www.naderb.org for more projects.

## Version 6.9.1

- Added playlist detection and selection interface
- Selective playlist download with checkboxes
- Individual video selection from playlists
- Enhanced playlist management
- Improved user experience for large playlists

## Version 6.9

- Enhanced quality display and selection
- Fixed MP3 audio downloads
- Silent console execution
- Improved settings interface
- Professional user interface
- Copyright compliance warnings
"""
    
    with open("release/README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("Release package created in 'release' folder")
    print(f"   - kartoshka-youtuber.exe")
    print(f"   - kartoshka-backend.exe")
    print(f"   - README.txt")
    if os.path.exists("icon.ico"):
        print(f"   - icon.ico")

def cleanup():
    """Clean up build files"""
    print("Cleaning up build files...")
    
    # Remove build directories
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name} directory")
    
    # Remove spec files
    for spec_file in ["backend.spec", "gui.spec"]:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"Removed {spec_file}")

def main():
    """Main build function"""
    print_header()
    
    # Check if we're on Windows
    if os.name != 'nt':
        print("This build script is designed for Windows only")
        print("   The executables will be built for the current platform")
        print()
    
    # Check dependencies
    check_dependencies()
    
    # Build applications
    if not build_backend():
        print("Build failed at backend stage")
        return
    
    if not build_gui():
        print("Build failed at GUI stage")
        return
    
    # Create release package
    create_release_package()
    
    print()
    print("Build completed successfully!")
    print("   You can find the executables in the 'release' folder")
    print()
    
    # Ask if user wants to clean up
    response = input("Clean up build files? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        cleanup()
        print("Cleanup completed")
    
    print()
    print("Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()
