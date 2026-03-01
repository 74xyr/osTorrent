from aria2_setup import install_aria2
from torrent_client import TorrentClient
import sys

# === FIX: PyExpat explizit importieren ===
import xml.parsers.expat
# =========================================

if __name__ == "__main__":
    if not getattr(sys, 'frozen', False):
        if not install_aria2():
            print("Setup Failed.")
            sys.exit(1)
            
    # LOGIK 3: Check auf Drag & Drop (Argumente)
    dropped_file = None
    if len(sys.argv) > 1:
        dropped_file = sys.argv[1]
        
    client = TorrentClient(startup_file=dropped_file)
    client.run()