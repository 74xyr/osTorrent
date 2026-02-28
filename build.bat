@echo off
title osTorrent Builder
color 0b

echo.
echo  Building osTorrent...
echo.

:: 1. Check Aria2c
if not exist "server\aria2c.exe" (
    python -c "from aria2_setup import install_aria2; install_aria2()"
)

:: 2. Check Icon (WICHTIG)
if not exist "os.ico" (
    color 0c
    echo  [ERROR] os.ico fehlt! Das Icon wird nicht gesetzt.
    echo  Bitte erstelle eine os.ico oder konvertiere die PNG.
    pause
    exit
)

pip install pyinstaller requests >nul

:: 3. Build (Ohne --strip, aber mit Icon)
python -m PyInstaller --noconfirm --onefile --console --clean ^
    --name "osTorrent" ^
    --icon "os.ico" ^
    --add-data "server\aria2c.exe;server" ^
    --add-data "os.ico;." ^
    main.py

if exist "dist\osTorrent.exe" (
    color 0a
    echo.
    echo  [SUCCESS] osTorrent.exe created.
    echo.
    copy /Y "dist\osTorrent.exe" "osTorrent.exe" >nul
    rmdir /S /Q "build"
    rmdir /S /Q "dist"
    del "osTorrent.spec"
    
    echo  TIPP: Wenn das Icon fehlt, verschiebe die .exe in einen
    echo        anderen Ordner (Windows Cache Problem).
) else (
    color 0c
    echo  [ERROR] Build failed.
)

pause