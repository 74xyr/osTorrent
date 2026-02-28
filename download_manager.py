import subprocess
import xmlrpc.client
import time
import threading
import os
import sys
import socket
import shutil
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TorrentData:
    gid: str
    name: str
    progress: float
    state_str: str
    download_speed: float
    eta: int
    save_path: str
    total_size: int

class DownloadManager:
    def __init__(self, config):
        self.config = config
        self.aria2_process = None
        self.rpc = None
        self.running = True
        self.lock = threading.Lock()
        self.torrents = {}
        
        # 1. Pfade definieren
        self.app_data = Path(os.getenv('LOCALAPPDATA')) / "osTorrent"
        self.aria2_local_path = self.app_data / "aria2c.exe"
        self.session_file = self.app_data / "session.txt"
        
        # 2. Ordner erstellen
        self.app_data.mkdir(parents=True, exist_ok=True)
        if not self.session_file.exists(): 
            try: self.session_file.touch()
            except: pass

        # 3. Aria2c extrahieren (installieren)
        self._install_engine()

        # 4. Starten
        # Alte Instanzen killen
        subprocess.run("taskkill /F /IM aria2c.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

        if not self._start_aria2_daemon():
            self._add_firewall_rule()
            self._start_aria2_daemon()

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _install_engine(self):
        """Kopiert aria2c.exe aus der PyInstaller-Exe nach LocalAppData"""
        # Wenn sie schon da ist, machen wir nichts (spart Zeit)
        if self.aria2_local_path.exists():
            return

        try:
            # Quelle finden (Innerhalb der exe)
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent
            
            source_path = base_path / "server" / "aria2c.exe"
            
            # Falls im server ordner nicht gefunden, fallback auf root (für dev mode)
            if not source_path.exists():
                source_path = base_path / "aria2c.exe"

            if source_path.exists():
                shutil.copy2(source_path, self.aria2_local_path)
        except: pass

    def _add_firewall_rule(self):
        try:
            cmd = f"New-NetFirewallRule -Program '{self.aria2_local_path}' -Action Allow -Profile Domain,Private,Public -DisplayName 'osTorrent Engine'"
            subprocess.run(["powershell", "-Command", cmd], creationflags=0x08000000)
        except: pass

    def _is_port_open(self, port=6800):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('localhost', port)) == 0

    def _start_aria2_daemon(self):
        if not self.aria2_local_path.exists(): return False
        
        cmd = [
            str(self.aria2_local_path), # Nutzt jetzt die exe in AppData
            "--enable-rpc=true",
            "--rpc-listen-all=false",
            "--rpc-allow-origin-all=true",
            "--rpc-listen-port=6800",
            "--max-connection-per-server=16",
            "--seed-time=0",
            "--quiet=true",
            "--follow-torrent=mem",
            f"--input-file={self.session_file}",
            f"--save-session={self.session_file}",
            "--save-session-interval=30"
        ]
        
        limit = self.config.get("download_limit")
        if limit > 0: cmd.append(f"--max-download-limit={limit}K")

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        try:
            self.aria2_process = subprocess.Popen(
                cmd, startupinfo=startupinfo,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except: return False
        
        for _ in range(10):
            if self._is_port_open(6800):
                try:
                    self.rpc = xmlrpc.client.ServerProxy("http://localhost:6800/rpc")
                    self.rpc.aria2.getVersion()
                    return True
                except: pass
            time.sleep(0.5)
        return False

    def is_downloading(self):
        if not self.rpc: return False
        try: return len(self.rpc.aria2.tellActive(["gid"])) > 0
        except: return False

    def add_magnet(self, magnet_link, save_path):
        if not self.rpc: self._start_aria2_daemon()
        if not self.rpc: return None
        try: return self.rpc.aria2.addUri([magnet_link], {"dir": save_path})
        except: return None

    def pause_torrent(self, gid):
        if self.rpc: self.rpc.aria2.pause(gid)

    def resume_torrent(self, gid):
        if self.rpc: self.rpc.aria2.unpause(gid)

    def remove_torrent(self, gid, delete_files=False):
        if not self.rpc: return
        try: self.rpc.aria2.remove(gid)
        except:
            try: self.rpc.aria2.removeDownloadResult(gid)
            except: pass

    def clear_finished(self):
        if not self.rpc: return
        with self.lock: current_gids = list(self.torrents.keys())
        for gid in current_gids:
            t = self.torrents[gid]
            if t.state_str in ["Complete", "Removed", "Error"]:
                try: self.rpc.aria2.removeDownloadResult(gid)
                except: pass

    def update_limit(self):
        if not self.rpc: return
        limit = self.config.get("download_limit")
        limit_str = f"{limit}K" if limit > 0 else "0"
        self.rpc.aria2.changeGlobalOption({"max-download-limit": limit_str})

    def get_all_torrents(self):
        with self.lock: return self.torrents.copy()

    def _monitor_loop(self):
        keys = ["gid", "status", "totalLength", "completedLength", "downloadSpeed", "dir", "bittorrent", "followedBy"]
        fail_count = 0
        
        while self.running:
            if not self.rpc:
                time.sleep(1)
                continue
                
            try:
                active = self.rpc.aria2.tellActive(keys)
                fail_count = 0
                
                waiting = self.rpc.aria2.tellWaiting(0, 100, keys)
                stopped = self.rpc.aria2.tellStopped(0, 100, keys)
                all_downloads = active + waiting + stopped
                current_torrents = {}
                
                for d in all_downloads:
                    gid, status_raw = d['gid'], d['status']
                    
                    is_meta_artifact = 'followedBy' in d
                    name = "Unbekannt / Metadata"
                    if 'bittorrent' in d and 'info' in d['bittorrent']:
                        name = d['bittorrent']['info'].get('name', name)
                    
                    if status_raw == 'complete' and name == "Unbekannt / Metadata": is_meta_artifact = True

                    if status_raw == 'complete' and is_meta_artifact:
                        try: self.rpc.aria2.removeDownloadResult(gid)
                        except: pass
                        continue 
                    
                    total = int(d['totalLength'])
                    done = int(d['completedLength'])
                    speed = int(d['downloadSpeed'])
                    progress = (done / total) * 100 if total > 0 else 0.0
                    
                    state_str = status_raw.capitalize()
                    if status_raw == 'active' and total == 0: state_str = "Metadata"
                    elif status_raw == 'active': state_str = "Downloading"
                    
                    eta = int((total - done) / speed) if speed > 0 and total > done else 0
                        
                    current_torrents[gid] = TorrentData(
                        gid=gid, name=name, progress=progress,
                        state_str=state_str, download_speed=speed,
                        eta=eta, save_path=d['dir'], total_size=total
                    )
                    
                    if status_raw == "complete" and self.config.get("auto_open_on_finish"): pass

                with self.lock: self.torrents = current_torrents
                
            except:
                fail_count += 1
                if fail_count > 5:
                    self._start_aria2_daemon()
                    fail_count = 0
            
            time.sleep(1)

    def open_folder(self, path):
        try:
            if os.name == 'nt': os.startfile(path)
            else: subprocess.run(["xdg-open", path])
        except: pass

    def shutdown(self):
        self.running = False
        if self.rpc:
            try: self.rpc.aria2.saveSession()
            except: pass
        try:
            subprocess.run("taskkill /F /IM aria2c.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
        except: pass