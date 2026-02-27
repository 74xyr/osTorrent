import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

def install_aria2():
    """Prüft auf aria2c.exe und installiert sie automatisch in den 'server' Ordner."""
    
    # Pfade definieren
    base_dir = Path(__file__).parent
    server_dir = base_dir / "server"
    aria2_exe = server_dir / "aria2c.exe"
    
    # URL für Aria2c Windows 64-bit (Github Release)
    DOWNLOAD_URL = "https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0-win-64bit-build1.zip"
    ZIP_FILENAME = "aria2.zip"
    
    # Prüfen ob bereits installiert
    if aria2_exe.exists():
        return True
        
    print("=" * 60)
    print("  SYSTEM: Aria2c Engine fehlt.")
    print("  Starte automatische Installation...")
    print("=" * 60)
    
    try:
        # 1. Server Ordner erstellen
        server_dir.mkdir(exist_ok=True)
        zip_path = server_dir / ZIP_FILENAME
        
        # 2. Herunterladen
        print(f"  [1/3] Lade Aria2c herunter... (Dies kann kurz dauern)")
        urllib.request.urlretrieve(DOWNLOAD_URL, zip_path)
        
        # 3. Entpacken
        print(f"  [2/3] Entpacke Dateien...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Wir suchen die exe im Zip (sie liegt meist in einem Unterordner)
            for file in zip_ref.namelist():
                if file.endswith("aria2c.exe"):
                    source = zip_ref.open(file)
                    target = open(aria2_exe, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    break
        
        # 4. Aufräumen
        print(f"  [3/3] Bereinige temporäre Dateien...")
        if zip_path.exists():
            os.remove(zip_path)
            
        print("\n  Installation erfolgreich! Starten...\n")
        return True
        
    except Exception as e:
        print(f"\n  FEHLER bei der Installation: {e}")
        print("  Bitte prüfe deine Internetverbindung.")
        return False