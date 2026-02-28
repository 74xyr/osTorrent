import sys
import time
import os
import requests
import msvcrt
import threading
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
        
        self.api_url = "http://5.231.29.228/heartbeat"
        self.online_users = 1
        self.stop_threads = False
        
        # Initialer Ping (Sofort)
        self.update_online_status()
        
        # Hintergrund Thread
        self.ping_thread = threading.Thread(target=self._online_heartbeat_loop, daemon=True)
        self.ping_thread.start()

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
                "dl_q": "Download this Torrent?",
                "nav_hint": "Use arrowkeys and enter to navigate",
                "setup_path_q": "Pick ur Path...",
                "explorer_closed": "Explorer got closed...",
                "path_fallback": "Default Path got selected, you can change it in Settings.",
                "users_online": "Users Online"
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
                "dl_q": "Torrent herunterladen?",
                "nav_hint": "Benutze Pfeiltasten und Enter zum Navigieren",
                "setup_path_q": "Wähle deinen Pfad...",
                "explorer_closed": "Explorer wurde geschlossen...",
                "path_fallback": "Standard Pfad gewählt, du kannst es in den Settings ändern.",
                "users_online": "Nutzer Online"
            }
        }

    def t(self, key):
        lang = self.config.get("language")
        if not lang: lang = "en"
        return self.txt.get(lang, self.txt["en"]).get(key, key)

    def update_online_status(self):
        """Einmaliger Ping für schnelles Update"""
        try:
            resp = requests.get(self.api_url, timeout=2)
            if resp.status_code == 200:
                self.online_users = resp.json().get("online", 1)
        except: pass

    def _online_heartbeat_loop(self):
        """Regelmäßiger Ping alle 60s"""
        while not self.stop_threads:
            self.update_online_status()
            for _ in range(60):
                if self.stop_threads: return
                time.sleep(1)

    def run(self):
        if self.config.get("first_run"): self.setup()
        while True:
            try:
                self.main_menu()
                break
            except KeyboardInterrupt:
                if self.check_exit(): break
        self.stop_threads = True
        self.dm.shutdown()

    def check_exit(self):
        if self.dm.is_downloading():
            self.ui.clear()
            if self.ui.confirm(self.t("exit_warn"), animate=True): return True
            return False
        return True

    # ... (setup, add_torrent_manual, start_download, explore_tab, download_list, manage_torrent, settings_menu bleiben unverändert) ...
    # Füge hier den Rest der Methoden ein, die wir in der vorherigen Version hatten.
    # Sie haben sich nicht geändert.
    
    def setup(self):
        self.ui.clear()
        self.ui.type_text("Welcome to", speed=0.05, color=self.ui.CYAN)
        print(self.ui.CYAN + self.ui.art["main"] + self.ui.RESET)
        self.ui.type_text("  Please pick ur language...", speed=0.03)
        options = ["English (EN)", "Deutsch (DE)"]
        selected = 0
        while True:
            self.ui.clear()
            print(self.ui.CYAN + "Welcome to" + self.ui.RESET)
            print(self.ui.CYAN + self.ui.art["main"] + self.ui.RESET)
            print(f"  Please pick ur language...")
            print()
            for i, opt in enumerate(options):
                prefix, color = "  ", self.ui.RESET
                if i == selected: prefix, color = "> ", self.ui.CYAN
                print(f"{color}{prefix}{opt}{self.ui.RESET}")
            key = self.ui.get_key()
            if key == 'up': selected = max(0, selected - 1)
            elif key == 'down': selected = min(1, selected + 1)
            elif key == 'enter': break
        lang = "en" if selected == 0 else "de"
        self.config.set("language", lang)
        self.ui.clear()
        print(self.ui.CYAN + self.ui.art["main"] + self.ui.RESET)
        self.ui.type_text(f"  {self.t('setup_path_q')}", speed=0.03)
        print()
        default = self.config.get("default_download_path")
        self.ui.type_text(f"  {self.t('choose_path')}: [{default}]", speed=0.02, color=self.ui.CYAN)
        if self.ui.confirm(self.t('change_q'), animate=True):
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            selected_path = filedialog.askdirectory(initialdir=default, title=self.t("choose_path"))
            root.destroy()
            if selected_path: self.config.set("default_download_path", selected_path)
            else:
                print()
                self.ui.type_text(f"  {self.t('explorer_closed')}", speed=0.03, color=self.ui.RED)
                self.ui.type_text(f"  {self.t('path_fallback')}", speed=0.03, color=self.ui.YELLOW)
                time.sleep(2)
        self.config.set("first_run", False)

    def main_menu(self):
        # Update User Count bei jedem Menü-Aufruf
        self.update_online_status()
        
        while True:
            explore_title = self.t("explore")
            options = [self.t("dl_torrent"), explore_title, self.t("dl_list"), self.t("settings")]
            user_text = f"{self.ui.GREEN}● {self.online_users} {self.t('users_online')}{self.ui.RESET}"
            hint_text = f"{user_text}  |  {self.t('nav_hint')}"
            
            idx = self.ui.select_menu("osTorrent", options, exit_text="EXIT", art_key="main", hint=hint_text, animate_hint=False)
            if idx == -1:
                if self.check_exit(): break
                else: continue
            if idx == 0: self.add_torrent_manual()
            elif idx == 1: self.explore_tab()
            elif idx == 2: self.download_list()
            elif idx == 3: self.settings_menu()

    def add_torrent_manual(self):
        self.ui.header("Download", art_key="main")
        magnet = self.ui.input(self.t("magnet_input"), animate=True)
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
            idx = self.ui.select_menu(title, display_list, exit_text=self.t("back"), art_key="explore")
            if idx == -1: break
            selected_item = data[idx]
            self.ui.clear()
            self.ui.header(title, art_key="explore")
            self.ui.type_text(f"\n  {selected_item['name']}", color=self.ui.CYAN)
            if self.ui.confirm(self.t("dl_q"), animate=True):
                self.start_download(selected_item['magnet'])

    def download_list(self):
        while True:
            self.ui.header(self.t("dl_list"), art_key="dl_list")
            torrents = list(self.dm.get_all_torrents().values())
            if not torrents: print(f"  {self.t('empty')}")
            else:
                for i, t in enumerate(torrents, 1): self.ui.print_torrent(i, t)
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
                sel_idx = self.ui.select_menu(self.t("menu_manage"), t_names, exit_text=self.t("back"), art_key="dl_list")
                if sel_idx != -1: self.manage_torrent(torrents[sel_idx])

    def manage_torrent(self, t):
        while True:
            self.ui.header(t.name[:50], art_key="dl_list")
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
                if self.ui.confirm(self.t("delete_q"), animate=True):
                    self.dm.remove_torrent(t.gid)
                    break

    def settings_menu(self):
        while True:
            c = self.config
            l = c.get("language")
            lang_label = "English" if l == "en" else "Deutsch"
            opts = [f"Path: {c.get('default_download_path')}", f"{self.t('limit')}: {c.get('download_limit')} KB/s", f"{self.t('lang')}: {lang_label}", self.t("clear_cache")]
            idx = self.ui.select_menu(self.t("settings"), opts, exit_text=self.t("back"), art_key="settings")
            if idx == -1: break
            if idx == 0:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                p = filedialog.askdirectory()
                root.destroy()
                if p: c.set("default_download_path", p)
            if idx == 1:
                self.ui.header("Limit", art_key="settings")
                inp = self.ui.input(self.t("new_limit"), animate=True)
                if inp.isdigit():
                    c.set("download_limit", int(inp))
                    self.dm.update_limit()
            if idx == 2: c.set("language", "de" if l == "en" else "en")
            if idx == 3:
                c.clear_cache()
                self.ui.message(self.t("cache_cleared"))