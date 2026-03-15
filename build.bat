@echo off
title Building Kartoshka Youtuber v6.9
color 0A
echo.
echo  ================================================
echo  🔥 Building Kartoshka Youtuber v6.9
echo  ================================================
echo  Created by NaderB - https://www.naderb.org
echo  A clean, modern YouTube downloader
echo  ================================================
echo.
echo  Building Python application...
echo.

python build.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  [SUCCESS] Build successful!
    echo  Executables created in 'release' folder
    echo.
) else (
    echo.
    echo  [ERROR] Build failed!
    echo  Please check the error messages above.
)

echo.
echo  Press any key to exit...
pause >nul



