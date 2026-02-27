@echo off
title osTorrent Builder (Fixed)
color 0b

echo ==========================================
echo      osTorrent Exe Builder
echo ==========================================
echo.

:: 1. Sicherstellen, dass Aria2c da ist
if not exist "server\aria2c.exe" (
    echo [INFO] Lade Aria2c herunter...
    python -c "from aria2_setup import install_aria2; install_aria2()"
)

if not exist "server\aria2c.exe" (
    color 0c
    echo [FEHLER] server/aria2c.exe fehlt!
    pause
    exit
)

:: 2. PyInstaller installieren (falls noch nicht da)
echo.
echo [INFO] Installiere Requirements...
pip install pyinstaller aiohttp
cls

:: 3. Exe bauen (via Python Modul)
echo.
echo [INFO] Erstelle osTorrent.exe...
echo Dies dauert einen Moment...
echo.

:: WICHTIG: Wir nutzen "python -m PyInstaller" statt nur "pyinstaller"
python -m PyInstaller --noconfirm --onefile --console --clean ^
    --name "osTorrent" ^
    --add-data "server\aria2c.exe;server" ^
    --hidden-import "aria2_setup" ^
    main.py

echo.
echo ==========================================
echo             STATUS BERICHT
echo ==========================================

if exist "dist\osTorrent.exe" (
    color 0a
    echo [ERFOLG] Die Datei wurde erstellt!
    echo.
    echo Kopiere Datei aus "dist" hierher...
    copy /Y "dist\osTorrent.exe" "osTorrent.exe"
    echo.
    echo Fertig! Deine "osTorrent.exe" ist bereit.
) else (
    color 0c
    echo [FEHLER] Die .exe wurde NICHT erstellt.
    echo Bitte schau oben nach Fehlermeldungen.
)

:: Aufräumen (optional)
if exist "osTorrent.spec" del "osTorrent.spec"
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"

pause