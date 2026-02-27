from aria2_setup import install_aria2
from torrent_client import TorrentClient
import sys

if __name__ == "__main__":
    if not install_aria2():
        print("Setup Failed.")
        sys.exit(1)
        
    client = TorrentClient()
    client.run()