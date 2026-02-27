import sys
import time
import os
from pathlib import Path
from ui import UI
from config_manager import ConfigManager
from download_manager import DownloadManager

class TorrentClient:
    def __init__(self):
        # 1. Config & UI ZUERST laden (verhindert den AttributeError)
        self.ui = UI()
        self.config = ConfigManager()

        # 2. Pfad zur aria2c.exe finden (Unterschied .py vs .exe)
        if getattr(sys, 'frozen', False):
            # Wenn wir als .exe laufen (PyInstaller Temp Ordner)
            base_path = Path(sys._MEIPASS)
        else:
            # Wenn wir als normales Skript laufen
            base_path = Path(__file__).parent
            
        # Wir suchen im "server" Ordner (so wie in build.bat definiert)
        self.aria2_path = base_path / "server" / "aria2c.exe"

        # Check ob Datei existiert
        if not self.aria2_path.exists():
            print(f"\n[CRITICAL ERROR] aria2c.exe not found at:")
            print(f"{self.aria2_path}")
            print("\nPlease rebuild the exe correctly.")
            input("Press Enter to exit...")
            sys.exit(1)

        # 3. Download Manager starten
        self.dm = DownloadManager(self.config)

    def run(self):
        if self.config.get("first_run"): 
            self.setup()
        
        try: 
            self.main_menu()
        finally: 
            self.dm.shutdown()

    def setup(self):
        self.ui.header()
        print("  Willkommen! Setup...")
        def_path = self.config.get("default_download_path")
        path = self.ui.input(f"Download Pfad [{def_path}]")
        if path: self.config.set("default_download_path", path)
        self.config.set("first_run", False)

    def main_menu(self):
        while True:
            self.ui.menu("Main Menu", ["Download Torrent", "Download List", "Settings"])
            c = self.ui.input("Wahl")
            if c == "1": self.add_torrent()
            elif c == "2": self.list_torrents()
            elif c == "3": self.settings()
            elif c == "0": break

    def add_torrent(self):
        self.ui.header()
        magnet = self.ui.input("Magnet Link")
        if not magnet.startswith("magnet:"): return
        
        save_path = self.config.get("default_download_path")
        if self.ui.input(f"Standardpfad ({save_path})? j/n") != 'j':
            p = self.ui.input("Pfad")
            if p: save_path = p
        
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            gid = self.dm.add_magnet(magnet, save_path)
            if gid: self.ui.message("Hinzugefügt!")
            else: self.ui.message("Fehler!")
        except Exception as e:
            self.ui.message(f"Fehler beim Ordner erstellen: {e}")

    def list_torrents(self):
        while True:
            self.ui.header()
            torrents = list(self.dm.get_all_torrents().values())
            
            if not torrents: 
                print("  Keine Torrents.")
            else:
                for i, t in enumerate(torrents, 1):
                    self.ui.print_torrent(i, t)
            
            print("-" * 70)
            print("  [C] Clear finished list")
            print("  [M] Manage Torrent")
            print("  [0] Zurück")
            print()
            
            rate = self.config.get("refresh_rate")
            key = self.ui.wait_for_input(rate)
            
            if key is None: continue 
            if key == '0': break
            if key == 'c':
                self.dm.clear_finished()
                continue
            if key == 'm' or key == '\r':
                c = self.ui.input("Nummer eingeben")
                if c.isdigit():
                    idx = int(c) - 1
                    if 0 <= idx < len(torrents):
                        self.manage(torrents[idx])

    def manage(self, t):
        while True:
            self.ui.header()
            print(f"  {self.ui.COLOR}{t.name}{self.ui.RESET}")
            print(f"  Status: {t.state_str}")
            print("-" * 70)
            
            opts = ["Pause" if t.state_str != "Paused" else "Resume", "Open Folder", "Remove"]
            for i, o in enumerate(opts, 1): print(f"  [{i}] {o}")
            print("\n  [0] Back")
            
            c = self.ui.input("Action")
            if c == '0': break
            if c == '1':
                if t.state_str == "Paused": self.dm.resume_torrent(t.gid)
                else: self.dm.pause_torrent(t.gid)
                break
            if c == '2': self.dm.open_folder(t.save_path)
            if c == '3':
                if self.ui.input("Sicher? j/n") == 'j':
                    self.dm.remove_torrent(t.gid)
                    break

    def settings(self):
        while True:
            self.ui.header()
            conf = self.config
            print(f"  1. Pfad: {conf.get('default_download_path')}")
            print(f"  2. Limit: {conf.get('download_limit')} KB/s")
            print(f"  3. Auto-Open: {conf.get('auto_open_on_finish')}")
            print(f"  4. Cache leeren")
            print(f"  5. Auto-Refresh: {conf.get('refresh_rate')}s (0 = durchgehend)")
            print("\n  0. Zurück")
            
            c = self.ui.input("Wahl")
            if c == '0': break
            elif c == '1': 
                p = self.ui.input("Pfad")
                if p: conf.set("default_download_path", p)
            elif c == '2':
                l = self.ui.input("Limit")
                if l.isdigit():
                    conf.set("download_limit", int(l))
                    self.dm.update_limit()
            elif c == '3':
                curr = conf.get("auto_open_on_finish")
                conf.set("auto_open_on_finish", not curr)
            elif c == '4':
                conf.clear_cache()
                self.ui.message("Cache geleert")
            elif c == '5':
                r = self.ui.input("Sekunden")
                if r.isdigit():
                    conf.set("refresh_rate", int(r))