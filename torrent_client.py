import sys
import time
import os
import requests
import msvcrt
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from ui import UI
from config_manager import ConfigManager
from download_manager import DownloadManager

class TorrentClient:
    def __init__(self):
        # Aria2c Check
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent
        
        exe_path = base_path / "server" / "aria2c.exe"
        if not exe_path.exists():
            exe_path = base_path / "aria2c.exe"
        
        if not exe_path.exists():
            print("CRITICAL: Aria2c missing.")
            sys.exit(1)

        self.ui = UI()
        self.config = ConfigManager()
        self.dm = DownloadManager(self.config)
        
        # Sprachen Strings
        self.txt = {
            "en": {
                "dl_torrent": "Download Torrent",
                "explore": "Explore",
                "explore_new": "Explore (NEW TORRENTS)",
                "dl_list": "Download List",
                "settings": "Settings",
                "choose_path": "Default Path is",
                "change_q": "Would you like to change it?",
                "exit_warn": "Downloads are running! Are you sure you want to quit osTorrent?",
                "added": "Torrent added successfully!",
                "err_magnet": "Invalid Magnet Link",
                "menu_clear": "Clear finished list",
                "menu_manage": "Manage Torrent (Press M or Enter)",
                "limit": "Download Limit"
            },
            "de": {
                "dl_torrent": "Torrent herunterladen",
                "explore": "Entdecken",
                "explore_new": "Entdecken (NEUE TORRENTS)",
                "dl_list": "Download Liste",
                "settings": "Einstellungen",
                "choose_path": "Standard Pfad ist",
                "change_q": "Möchten Sie diesen ändern?",
                "exit_warn": "Es werden gerade Torrents installiert. Sind Sie sicher, dass Sie osTorrent beenden möchten?",
                "added": "Torrent erfolgreich hinzugefügt!",
                "err_magnet": "Ungültiger Magnet Link",
                "menu_clear": "Liste bereinigen",
                "menu_manage": "Verwalten (Drücke M oder Enter)",
                "limit": "Download Limit"
            }
        }

    def t(self, key):
        """Übersetzer Helper"""
        lang = self.config.get("language")
        if not lang: lang = "en"
        return self.txt.get(lang, self.txt["en"]).get(key, key)

    def run(self):
        if self.config.get("first_run"):
            self.setup()
        
        while True:
            try:
                self.main_menu()
                break # Wenn main menu returned, beenden
            except KeyboardInterrupt:
                if self.check_exit():
                    break
        
        self.dm.shutdown()

    def check_exit(self):
        """Prüft ob Downloads laufen vor Exit"""
        if self.dm.is_downloading():
            self.ui.clear()
            if self.ui.confirm(self.t("exit_warn")):
                return True
            return False
        return True

    def setup(self):
        self.ui.clear()
        print(self.ui.CYAN + "Welcome / Willkommen" + self.ui.RESET)
        print()
        
        # 1. Sprache
        options = ["English (EN)", "Deutsch (DE)"]
        idx = self.ui.select_menu("Select your language", options, exit_option=False)
        
        lang = "en" if idx == 0 else "de"
        self.config.set("language", lang)
        
        # 2. Pfad
        self.ui.clear()
        default = self.config.get("default_download_path")
        print(f"\n  {self.t('choose_path')}: [{self.ui.CYAN}{default}{self.ui.RESET}]")
        
        if self.ui.confirm(self.t('change_q')):
            # Folder Dialog öffnen (verstecktes TK Fenster)
            root = tk.Tk()
            root.withdraw()
            # Fenster in den Vordergrund zwingen
            root.attributes('-topmost', True)
            
            selected_path = filedialog.askdirectory(initialdir=default, title=self.t("choose_path"))
            root.destroy()
            
            if selected_path:
                self.config.set("default_download_path", selected_path)
        
        self.config.set("first_run", False)

    def main_menu(self):
        while True:
            # Check for new torrents
            has_new = False
            try:
                # Schneller Check ob wir überhaupt neue haben könnten
                pass # (Logik passiert im Explore Tab Aufruf)
            except: pass

            explore_title = self.t("explore")
            # Wir checken das Explore label später dynamisch
            
            options = [
                self.t("dl_torrent"),
                explore_title, # Placeholder, wird live nicht geupdatet im Main Menu Array, aber ok
                self.t("dl_list"),
                self.t("settings")
            ]
            
            idx = self.ui.select_menu("osTorrent", options)
            
            if idx == -1: # Exit
                if self.check_exit(): break
                else: continue

            if idx == 0: self.add_torrent_manual()
            elif idx == 1: self.explore_tab()
            elif idx == 2: self.download_list()
            elif idx == 3: self.settings_menu()

    def add_torrent_manual(self):
        self.ui.header()
        magnet = self.ui.input("Magnet Link") # Hier noch old-school input
        if not magnet.startswith("magnet:"): 
            self.ui.message(self.t("err_magnet"), self.ui.RED)
            return
        
        self.start_download(magnet)

    def start_download(self, magnet):
        path = self.config.get("default_download_path")
        gid = self.dm.add_magnet(magnet, path)
        if gid: self.ui.message(self.t("added"), self.ui.GREEN)
        else: self.ui.message("Error", self.ui.RED)

    def explore_tab(self):
        url = "https://raw.githubusercontent.com/74xyr/osTorrent/main/torrents.json"
        try:
            self.ui.header("Lade Torrents...")
            resp = requests.get(url, timeout=5)
            data = resp.json()
        except Exception as e:
            self.ui.message(f"Connection Error: {e}", self.ui.RED)
            return

        while True:
            # Check New Torrents
            new_exists = False
            display_list = []
            
            for item in data:
                name = item['name']
                magnet = item['magnet']
                
                # Check ob neu
                if self.config.is_torrent_new(magnet):
                    name = f"{self.ui.YELLOW}[NEW]{self.ui.RESET} {name}"
                    new_exists = True
                
                display_list.append(name)
            
            title = self.t("explore")
            if new_exists:
                title = self.t("explore_new")

            # Zeige Liste
            idx = self.ui.select_menu(title, display_list)
            
            if idx == -1: break # Zurück
            
            # Torrent ausgewählt
            selected_item = data[idx]
            self.ui.clear()
            print(f"\n  {self.ui.CYAN}{selected_item['name']}{self.ui.RESET}")
            if self.ui.confirm("Download this Torrent?"):
                self.start_download(selected_item['magnet'])

    def download_list(self):
        while True:
            self.ui.header(self.t("dl_list"))
            torrents = list(self.dm.get_all_torrents().values())
            
            if not torrents: print("  (Empty)")
            else:
                for i, t in enumerate(torrents, 1):
                    self.ui.print_torrent(i, t)
            
            print("-" * 75)
            print(f"  [C] {self.t('menu_clear')}")
            print(f"  [M] {self.t('menu_manage')}")
            print("  [0] Back")
            
            rate = self.config.get("refresh_rate")
            key = self.ui.wait_for_input(rate if rate > 0 else 0.1) # UI update
            
            if key is None: continue
            
            if key == '0': break
            if key == 'c': self.dm.clear_finished()
            if key == 'm' or key == 'enter':
                # Einfacher Manage Selector
                t_names = [f"{t.state_str}: {t.name}" for t in torrents]
                if not t_names: continue
                
                sel_idx = self.ui.select_menu("Manage Torrent", t_names)
                if sel_idx != -1:
                    self.manage_torrent(torrents[sel_idx])

    def manage_torrent(self, t):
        while True:
            self.ui.header(t.name[:50])
            status = "Pause" if t.state_str != "Paused" else "Resume"
            opts = [status, "Open Folder", "Remove"]
            
            idx = self.ui.select_menu(f"Status: {t.state_str}", opts)
            if idx == -1: break
            
            if idx == 0:
                if t.state_str == "Paused": self.dm.resume_torrent(t.gid)
                else: self.dm.pause_torrent(t.gid)
                break
            if idx == 1: 
                self.dm.open_folder(t.save_path)
            if idx == 2:
                if self.ui.confirm("Delete Torrent?"):
                    self.dm.remove_torrent(t.gid)
                    break

    def settings_menu(self):
        while True:
            c = self.config
            l = c.get("language")
            opts = [
                f"Path: {c.get('default_download_path')}",
                f"{self.t('limit')}: {c.get('download_limit')} KB/s",
                f"Language: {l}",
                "Clear Cache"
            ]
            
            idx = self.ui.select_menu(self.t("settings"), opts)
            if idx == -1: break
            
            if idx == 0:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                p = filedialog.askdirectory()
                root.destroy()
                if p: c.set("default_download_path", p)
            
            if idx == 1:
                self.ui.header()
                inp = input("  New Limit (KB/s): ")
                if inp.isdigit():
                    c.set("download_limit", int(inp))
                    self.dm.update_limit()
            
            if idx == 2:
                new_lang = "de" if l == "en" else "en"
                c.set("language", new_lang)
            
            if idx == 3:
                c.clear_cache()
                self.ui.message("Cache Cleared.")