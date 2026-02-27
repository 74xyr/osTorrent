@echo off
title osTorrent Builder
color 0b

echo ==========================================
echo      osTorrent Exe Builder (PyInstaller)
echo ==========================================
echo.

:: 1. Aria2c sicherstellen (wird in die Exe gepackt)
echo [1/4] Pruefe Aria2c...
if not exist "server\aria2c.exe" (
    echo Aria2c fehlt. Starte Downloader script...
    python -c "from aria2_setup import install_aria2; install_aria2()"
)

if not exist "server\aria2c.exe" (
    color 0c
    echo FEHLER: Aria2c konnte nicht geladen werden.
    pause
    exit
)

:: 2. PyInstaller installieren
echo.
echo [2/4] Installiere PyInstaller...
pip install pyinstaller aiohttp
cls

:: 3. Exe bauen
echo.
echo [3/4] Erstelle osTorrent.exe...
echo Dies kann einen Moment dauern...
echo.

:: --onefile: Alles in eine Datei
:: --name: Name der Exe
:: --add-data: Fügt den server Ordner (mit aria2c) in die Exe ein
:: --clean: Cache leeren
pyinstaller --noconfirm --onefile --console --clean ^
    --name "osTorrent" ^
    --add-data "server;server" ^
    main.py

:: 4. Aufräumen und Verschieben
echo.
echo [4/4] Raeume auf...
move /Y "dist\osTorrent.exe" "osTorrent.exe"
rmdir /S /Q build
rmdir /S /Q dist
del osTorrent.spec

cls
color 0a
echo ==========================================
echo             FERTIG!
echo ==========================================
echo.
echo Die Datei "osTorrent.exe" wurde erstellt.
echo Du kannst diese Datei nun an Freunde senden.
echo Sie benoetigen KEIN Python und KEINE Installation.
echo.
pause