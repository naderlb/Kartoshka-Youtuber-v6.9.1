#!/usr/bin/env python3
"""
Build script for Kartoshka Youtuber v6.9.2
Creates standalone executables for Windows (C# GUI + Python backend)
Created by NaderB - https://www.naderb.org
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

VERSION = "6.9.2"


def print_header():
    print("=" * 50)
    print(f"Building Kartoshka Youtuber v{VERSION}")
    print("=" * 50)
    print("Created by NaderB - https://www.naderb.org")
    print("=" * 50)
    print()


def check_dependencies():
    print("Checking Python dependencies...")
    if os.path.exists("requirements.txt"):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("Python requirements installed")
    print()

    print("Checking .NET SDK...")
    try:
        subprocess.run(["dotnet", "--version"], check=True, capture_output=True)
        print(".NET SDK found")
    except Exception as e:
        print(f".NET SDK not found: {e}")
        print("Install .NET 8+ SDK to build the GUI.")
        return False
    print()
    return True


def build_backend():
    print("Building backend executable (PyInstaller)...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "kartoshka-backend",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--hidden-import", "ffmpeg",
        "--hidden-import", "yt_dlp",
        "--noconfirm",
        "backend.py",
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Backend built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Backend build failed: {e}")
        return False


def build_gui():
    print("Building GUI executable (dotnet publish)...")
    publish_dir = Path("dist") / "gui-publish"
    if publish_dir.exists():
        shutil.rmtree(publish_dir)

    cmd = [
        "dotnet", "publish",
        "KartoshkaYoutuber.csproj",
        "-c", "Release",
        "-r", "win-x64",
        "--self-contained", "true",
        "/p:PublishSingleFile=true",
        "/p:IncludeNativeLibrariesForSelfExtract=true",
        "/p:EnableCompressionInSingleFile=true",
        "-o", str(publish_dir),
    ]
    try:
        subprocess.run(cmd, check=True)
        exe = publish_dir / "kartoshka-youtuber.exe"
        if not exe.exists():
            # Fallback if assembly name differs
            candidates = list(publish_dir.glob("*.exe"))
            if not candidates:
                print("GUI exe not found after publish")
                return False
            exe = candidates[0]
        dest = Path("dist") / "kartoshka-youtuber.exe"
        shutil.copy2(exe, dest)
        print(f"GUI built successfully -> {dest}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"GUI build failed: {e}")
        return False


def create_release_package():
    print("Creating release package...")
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    gui_src = Path("dist") / "kartoshka-youtuber.exe"
    backend_src = Path("dist") / "kartoshka-backend.exe"
    if not gui_src.exists() or not backend_src.exists():
        print("Missing built executables in dist/")
        return False

    shutil.copy2(gui_src, release_dir / "kartoshka-youtuber.exe")
    shutil.copy2(backend_src, release_dir / "kartoshka-backend.exe")

    # Ship Python backend next to GUI for easier debugging / fallback
    shutil.copy2("backend.py", release_dir / "backend.py")
    if os.path.exists("requirements.txt"):
        shutil.copy2("requirements.txt", release_dir / "requirements.txt")

    if os.path.exists("icon.ico"):
        shutil.copy2("icon.ico", release_dir / "icon.ico")

    # Copy ffmpeg if present (skip if locked by another process)
    for ffmpeg_name in ("ffmpeg.exe",):
        for candidate in (Path(ffmpeg_name), Path("release") / ffmpeg_name, Path("bin") / ffmpeg_name):
            if candidate.exists() and candidate.resolve() != (release_dir / "ffmpeg.exe").resolve():
                try:
                    shutil.copy2(candidate, release_dir / "ffmpeg.exe")
                except PermissionError:
                    print(f"Skipped ffmpeg copy (file in use): {candidate}")
                break
            elif candidate.exists() and candidate.resolve() == (release_dir / "ffmpeg.exe").resolve():
                # Already in release — nothing to do
                break

    readme_content = f"""# Kartoshka Youtuber v{VERSION}

A YouTube downloader with a modern WPF GUI.

Created by NaderB - https://www.naderb.org

## How to Use

1. Keep these files in the same folder:
   - kartoshka-youtuber.exe  (GUI)
   - kartoshka-backend.exe   (downloader)
   - ffmpeg.exe              (optional but recommended for MP3 / merge)
2. Run kartoshka-youtuber.exe
3. Paste a YouTube URL (video or playlist / Mix)
4. Click Get Info
5. For playlists: select songs (or Select All), then Download Selected
6. Songs download one at a time with a short pause between each

## Version {VERSION}

- Playlist / Mix support with selectable track list
- One-by-one downloads with pause between songs
- C# WPF GUI (.NET 8 self-contained) + Python/yt-dlp backend

## Notice

For educational / personal use only. Only download content you own or have permission to download.
"""
    (release_dir / "README.txt").write_text(readme_content, encoding="utf-8")

    print("Release package ready in 'release/':")
    for name in sorted(os.listdir(release_dir)):
        size = (release_dir / name).stat().st_size
        print(f"  - {name} ({size:,} bytes)")
    return True


def cleanup():
    print("Cleaning up build files...")
    for dir_name in ("build", "dist"):
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}/")


def main():
    print_header()
    if not check_dependencies():
        sys.exit(1)

    if not build_backend():
        print("Build failed at backend stage")
        sys.exit(1)

    if not build_gui():
        print("Build failed at GUI stage")
        sys.exit(1)

    if not create_release_package():
        print("Failed to create release package")
        sys.exit(1)

    # Non-interactive cleanup (CI / agent friendly)
    auto_clean = "--clean" in sys.argv or os.environ.get("KARTOSHKA_CLEAN") == "1"
    if auto_clean:
        cleanup()
    else:
        print()
        print("Tip: re-run with --clean to remove build/ and dist/")

    print()
    print(f"Build completed successfully! v{VERSION}")
    print("Executables are in the 'release' folder.")


if __name__ == "__main__":
    main()
