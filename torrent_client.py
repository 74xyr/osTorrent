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
        if getattr(sys, 'frozen', False): base_path = Path(sys._MEIPASS)
        else: base_path = Path(__file__).parent
        exe_path = base_path / "server" / "aria2c.exe"
        if not exe_path.exists(): exe_path = base_path / "aria2c.exe"
        if not exe_path.exists(): sys.exit(1)

        self.ui = UI()
        self.config = ConfigManager()
        self.dm = DownloadManager(self.config)
        
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
                "menu_manage": "Manage Torrent",
                "limit": "Download Limit",
                "back": "Back",
                "empty": "(Empty)",
                "status": "Status",
                "open_folder": "Open Folder",
                "remove": "Remove",
                "delete_q": "Delete Torrent?",
                "lang": "Language",
                "clear_cache": "Clear Cache",
                "cache_cleared": "Cache Cleared.",
                "magnet_input": "Magnet Link",
                "err_folder": "Error creating folder",
                "new_limit": "New Limit (KB/s)",
                "pause": "Pause",
                "resume": "Resume",
                "dl_q": "Download this Torrent?"
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
                "menu_manage": "Verwalten",
                "limit": "Download Limit",
                "back": "Zurück",
                "empty": "(Leer)",
                "status": "Status",
                "open_folder": "Ordner öffnen",
                "remove": "Entfernen",
                "delete_q": "Torrent löschen?",
                "lang": "Sprache",
                "clear_cache": "Cache leeren",
                "cache_cleared": "Cache geleert.",
                "magnet_input": "Magnet Link",
                "err_folder": "Fehler beim Ordner erstellen",
                "new_limit": "Neues Limit (KB/s)",
                "pause": "Pausieren",
                "resume": "Fortsetzen",
                "dl_q": "Torrent herunterladen?"
            }
        }

    def t(self, key):
        lang = self.config.get("language")
        if not lang: lang = "en"
        return self.txt.get(lang, self.txt["en"]).get(key, key)

    def run(self):
        if self.config.get("first_run"): self.setup()
        while True:
            try:
                self.main_menu()
                break
            except KeyboardInterrupt:
                if self.check_exit(): break
        self.dm.shutdown()

    def check_exit(self):
        if self.dm.is_downloading():
            self.ui.clear()
            if self.ui.confirm(self.t("exit_warn")): return True
            return False
        return True

    def setup(self):
        # Hier nutzen wir noch das Standard-Logo (main)
        self.ui.header("osTorrent", art_key="main")
        print(self.ui.CYAN + "Welcome / Willkommen" + self.ui.RESET)
        print()
        idx = self.ui.select_menu("Select your language", ["English (EN)", "Deutsch (DE)"], exit_text="Exit", art_key="main")
        if idx == -1: sys.exit(0)
        
        lang = "en" if idx == 0 else "de"
        self.config.set("language", lang)
        
        self.ui.header("osTorrent", art_key="main")
        default = self.config.get("default_download_path")
        print(f"\n  {self.t('choose_path')}: [{self.ui.CYAN}{default}{self.ui.RESET}]")
        
        if self.ui.confirm(self.t('change_q')):
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            selected_path = filedialog.askdirectory(initialdir=default, title=self.t("choose_path"))
            root.destroy()
            if selected_path: self.config.set("default_download_path", selected_path)
        
        self.config.set("first_run", False)

    def main_menu(self):
        while True:
            explore_title = self.t("explore")
            options = [self.t("dl_torrent"), explore_title, self.t("dl_list"), self.t("settings")]
            
            # Hier Logo anzeigen
            idx = self.ui.select_menu("osTorrent", options, exit_text="Exit", art_key="main")
            
            if idx == -1:
                if self.check_exit(): break
                else: continue

            if idx == 0: self.add_torrent_manual()
            elif idx == 1: self.explore_tab()
            elif idx == 2: self.download_list()
            elif idx == 3: self.settings_menu()

    def add_torrent_manual(self):
        # Nutzt auch das Main Logo, da es kein eigenes Art für "Add" gab
        self.ui.header("Download", art_key="main")
        magnet = self.ui.input(self.t("magnet_input"))
        if not magnet.startswith("magnet:"): 
            self.ui.message(self.t("err_magnet"), self.ui.RED)
            return
        self.start_download(magnet)

    def start_download(self, magnet):
        path = self.config.get("default_download_path")
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            gid = self.dm.add_magnet(magnet, path)
            if gid: self.ui.message(self.t("added"), self.ui.GREEN)
            else: self.ui.message("Error", self.ui.RED)
        except Exception as e:
            self.ui.message(f"{self.t('err_folder')}: {e}", self.ui.RED)

    def explore_tab(self):
        url = "https://raw.githubusercontent.com/74xyr/osTorrent/main/torrents.json"
        try:
            # Hier "Loading..." ASCII Art
            self.ui.header("Loading...", art_key="loading")
            resp = requests.get(url, timeout=5)
            data = resp.json()
        except Exception as e:
            self.ui.message(f"Connection Error: {e}", self.ui.RED)
            return

        while True:
            new_exists = False
            display_list = []
            for item in data:
                name = item['name']
                magnet = item['magnet']
                if self.config.is_torrent_new(magnet):
                    name = f"{self.ui.YELLOW}[NEW]{self.ui.RESET} {name}"
                    new_exists = True
                display_list.append(name)
            
            title = self.t("explore_new") if new_exists else self.t("explore")
            
            # Hier "Explore" ASCII Art
            idx = self.ui.select_menu(title, display_list, exit_text=self.t("back"), art_key="explore")
            if idx == -1: break
            
            selected_item = data[idx]
            self.ui.clear()
            self.ui.header(title, art_key="explore") # Header behalten
            print(f"\n  {self.ui.CYAN}{selected_item['name']}{self.ui.RESET}")
            if self.ui.confirm(self.t("dl_q")):
                self.start_download(selected_item['magnet'])

    def download_list(self):
        while True:
            # Hier "Download list" ASCII Art
            self.ui.header(self.t("dl_list"), art_key="dl_list")
            torrents = list(self.dm.get_all_torrents().values())
            
            if not torrents: print(f"  {self.t('empty')}")
            else:
                for i, t in enumerate(torrents, 1):
                    self.ui.print_torrent(i, t)
            
            print("-" * 75)
            print(f"  [C] {self.t('menu_clear')}")
            print(f"  [M] {self.t('menu_manage')}")
            print(f"  [0] {self.t('back')}")
            
            rate = self.config.get("refresh_rate")
            key = self.ui.wait_for_input(rate if rate > 0 else 0.1)
            
            if key is None: continue
            if key == '0': break
            if key == 'c': self.dm.clear_finished()
            if key == 'm' or key == 'enter':
                t_names = [f"{t.state_str}: {t.name}" for t in torrents]
                if not t_names: continue
                # Bei Manage Liste behalten wir das Art
                sel_idx = self.ui.select_menu(self.t("menu_manage"), t_names, exit_text=self.t("back"), art_key="dl_list")
                if sel_idx != -1: self.manage_torrent(torrents[sel_idx])

    def manage_torrent(self, t):
        while True:
            self.ui.header(t.name[:50], art_key="dl_list") # Auch hier DL List Art
            status = self.t("pause") if t.state_str != "Paused" else self.t("resume")
            opts = [status, self.t("open_folder"), self.t("remove")]
            
            idx = self.ui.select_menu(f"{self.t('status')}: {t.state_str}", opts, exit_text=self.t("back"), art_key="dl_list")
            if idx == -1: break
            
            if idx == 0:
                if t.state_str == "Paused": self.dm.resume_torrent(t.gid)
                else: self.dm.pause_torrent(t.gid)
                break
            if idx == 1: self.dm.open_folder(t.save_path)
            if idx == 2:
                if self.ui.confirm(self.t("delete_q")):
                    self.dm.remove_torrent(t.gid)
                    break

    def settings_menu(self):
        while True:
            c = self.config
            l = c.get("language")
            lang_label = "English" if l == "en" else "Deutsch"
            opts = [
                f"Path: {c.get('default_download_path')}",
                f"{self.t('limit')}: {c.get('download_limit')} KB/s",
                f"{self.t('lang')}: {lang_label}",
                self.t("clear_cache")
            ]
            
            # Hier "Settings" ASCII Art
            idx = self.ui.select_menu(self.t("settings"), opts, exit_text=self.t("back"), art_key="settings")
            if idx == -1: break
            
            if idx == 0:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                p = filedialog.askdirectory()
                root.destroy()
                if p: c.set("default_download_path", p)
            if idx == 1:
                self.ui.header("Limit", art_key="settings")
                inp = self.ui.input(self.t("new_limit"))
                if inp.isdigit():
                    c.set("download_limit", int(inp))
                    self.dm.update_limit()
            if idx == 2:
                c.set("language", "de" if l == "en" else "en")
            if idx == 3:
                c.clear_cache()
                self.ui.message(self.t("cache_cleared"))