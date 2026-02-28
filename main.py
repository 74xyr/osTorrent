from aria2_setup import install_aria2
from torrent_client import TorrentClient
import sys

# === FIX: PyExpat explizit importieren ===
import xml.parsers.expat
# =========================================

if __name__ == "__main__":
    # Wenn wir als Exe laufen, überspringen wir setup hier,
    # da torrent_client.py das jetzt regelt (Install to AppData)
    if not getattr(sys, 'frozen', False):
        if not install_aria2():
            print("Setup Failed.")
            sys.exit(1)
        
    client = TorrentClient()
    client.run()