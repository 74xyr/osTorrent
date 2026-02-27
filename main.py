import sys
from aria2_setup import install_aria2
from torrent_client import TorrentClient

if __name__ == "__main__":
    # 1. Auto-Installation ausführen
    success = install_aria2()
    
    if not success:
        print("Kritischer Fehler: Konnte Aria2c nicht installieren.")
        input("Drücke Enter zum Beenden...")
        sys.exit(1)

    # 2. Client starten
    try:
        client = TorrentClient()
        client.run()
    except KeyboardInterrupt:
        pass