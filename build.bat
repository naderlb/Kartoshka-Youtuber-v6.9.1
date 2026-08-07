@echo off
title Building Kartoshka Youtuber v6.9.2
color 0A
echo.
echo  ================================================
echo  Building Kartoshka Youtuber v6.9.2
echo  ================================================
echo  Created by NaderB - https://www.naderb.org
echo  ================================================
echo.

python build.py --clean
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
pause
