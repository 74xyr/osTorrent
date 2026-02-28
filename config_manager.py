import json
import os
import shutil
import time
import sys
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # Pfad: %LOCALAPPDATA%/osTorrent
        self.app_data = Path(os.getenv('LOCALAPPDATA')) / "osTorrent"
        self.config_file = self.app_data / "config.json"
        self.seen_file = self.app_data / "seen_torrents.json"
        
        self.default_config = {
            "language": "",
            "default_download_path": str(Path.home() / "Downloads"),
            "download_limit": 0,
            "auto_open_on_finish": False,
            "refresh_rate": 3,
            "first_run": True,
            "installed": False # Neu: Merkt sich ob installiert
        }
        
        self.config = self._load_config()
        self.seen_torrents = self._load_seen()

    def _ensure_folders(self):
        self.app_data.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        self._ensure_folders()
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.default_config, **json.load(f)}
            except:
                return self.default_config.copy()
        return self.default_config.copy()

    def _load_seen(self):
        if self.seen_file.exists():
            try:
                with open(self.seen_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save(self):
        self._ensure_folders()
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def save_seen(self):
        self._ensure_folders()
        with open(self.seen_file, 'w', encoding='utf-8') as f:
            json.dump(self.seen_torrents, f, indent=4)

    def get(self, key):
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def mark_torrent_seen(self, magnet):
        import hashlib
        h = hashlib.md5(magnet.encode()).hexdigest()
        if h not in self.seen_torrents:
            self.seen_torrents[h] = time.time()
            self.save_seen()
    
    def is_torrent_new(self, magnet):
        import hashlib
        h = hashlib.md5(magnet.encode()).hexdigest()
        if h not in self.seen_torrents:
            self.mark_torrent_seen(magnet)
            return True
        if time.time() - self.seen_torrents[h] < 21600:
            return True
        return False

    def clear_cache(self):
        """Löscht alles in AppData/osTorrent und startet neu"""
        try:
            # Wir können den Ordner nicht löschen während wir drin sind/loggen
            # Also löschen wir nur den Inhalt außer der Exe selbst (falls sie dort läuft)
            for item in self.app_data.iterdir():
                if item.is_file():
                    if item.name != "osTorrent.exe" and item.name != "aria2c.exe":
                        item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            return True
        except: return False