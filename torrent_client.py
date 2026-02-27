import sys
import time
import os
from pathlib import Path
from ui import UI
from config_manager import ConfigManager
from download_manager import DownloadManager

class TorrentClient:
    def __init__(self):
        self.ui = UI()
        self.config = ConfigManager()
        self.dm = DownloadManager(self.config)

    def run(self):
        if self.config.get("first_run"): self.setup()
        try: self.main_menu()
        finally: self.dm.shutdown()

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
        
        Path(save_path).mkdir(parents=True, exist_ok=True)
        gid = self.dm.add_magnet(magnet, save_path)
        if gid: self.ui.message("Hinzugefügt!")
        else: self.ui.message("Fehler!")

    def list_torrents(self):
        while True:
            self.ui.header()
            
            # Torrents holen
            torrents = list(self.dm.get_all_torrents().values())
            
            if not torrents: 
                print("  Keine Torrents.")
            else:
                for i, t in enumerate(torrents, 1):
                    self.ui.print_torrent(i, t)
            
            print("-" * 70)
            print("  [C] Clear Finished List (Hotkey)")
            print("  [M] Manage Torrent (Pause/Delete...)")
            print("  [0] Zurück")
            print()
            print("  Auto-Refresh in 3s... (Drücke Taste für Menü)")
            
            # Wartet 3 Sekunden oder bis Taste gedrückt wird
            key = self.ui.wait_for_input(3)
            
            # === LOGIK ===
            
            # 1. Kein Key gedrückt (Timeout) -> Loop startet neu (Refresh)
            if key is None:
                continue
                
            # 2. '0' gedrückt -> Zurück
            if key == '0':
                break
                
            # 3. 'c' gedrückt -> Liste säubern
            if key == 'c':
                self.dm.clear_finished()
                # Sofortiger Refresh ohne Warten
                continue
                
            # 4. 'm' oder Enter gedrückt -> Torrent auswählen
            if key == 'm' or key == '\r': # \r ist Enter
                # Wir stoppen den Refresh, um Eingabe zu ermöglichen
                c = self.ui.input("Nummer eingeben")
                if c.isdigit():
                    idx = int(c) - 1
                    if 0 <= idx < len(torrents):
                        self.manage(torrents[idx])

    def manage(self, t):
        while True:
            self.ui.header()
            print(f"  {t.name}\n  Status: {t.state_str}")
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
            print(f"  1. Path: {self.config.get('default_download_path')}")
            print(f"  2. Limit: {self.config.get('download_limit')} KB/s")
            print(f"  3. Cache Clear")
            print("\n  0. Back")
            c = self.ui.input("Wahl")
            if c == '0': break
            if c == '1': 
                p = self.ui.input("Pfad")
                if p: self.config.set("default_download_path", p)
            if c == '2':
                l = self.ui.input("Limit")
                if l.isdigit():
                    self.config.set("download_limit", int(l))
                    self.dm.update_limit()
            if c == '3':
                self.config.clear_cache()
                self.ui.message("Cache geleert")