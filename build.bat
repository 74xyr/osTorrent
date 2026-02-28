@echo off
title osTorrent Builder
color 0b

echo.
echo  Building osTorrent...
echo.

if not exist "server\aria2c.exe" (
    python -c "from aria2_setup import install_aria2; install_aria2()"
)

pip install pyinstaller requests winshell pywin32 >nul

python -m PyInstaller --noconfirm --onefile --console --clean ^
    --name "osTorrent" ^
    --icon "os.ico" ^
    --hidden-import "xml.parsers.expat" ^
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
) else (
    color 0c
    echo  [ERROR] Build failed.
)

pause