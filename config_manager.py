import json
import os
import shutil
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.documents_path = Path.home() / "Documents"
        self.app_folder = self.documents_path / "osTorrent"
        self.config_file = self.app_folder / "config.json"
        self.cache_folder = self.app_folder / "cache"
        
        self.default_config = {
            "default_download_path": str(Path.home() / "Downloads"),
            "download_limit": 0,
            "auto_open_on_finish": False,
            "refresh_rate": 3,  # NEU: Standard 3 Sekunden
            "first_run": True
        }
        self.config = self._load_config()

    def _ensure_folders(self):
        self.app_folder.mkdir(parents=True, exist_ok=True)
        self.cache_folder.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        self._ensure_folders()
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return {**self.default_config, **json.load(f)}
            except:
                return self.default_config.copy()
        return self.default_config.copy()

    def save(self):
        self._ensure_folders()
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def clear_cache(self):
        if self.cache_folder.exists():
            shutil.rmtree(self.cache_folder)
            self.cache_folder.mkdir(parents=True, exist_ok=True)