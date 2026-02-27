import subprocess
import xmlrpc.client
import time
import threading
import os
import signal
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
        
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent

        self.aria2_path = str(base_path / "server" / "aria2c.exe")
        
        self._start_aria2_daemon()

    def _start_aria2_daemon(self):
        if not os.path.exists(self.aria2_path):
            return

        cmd = [
            self.aria2_path,
            "--enable-rpc=true",
            "--rpc-listen-all=false",
            "--rpc-allow-origin-all=true",
            "--rpc-listen-port=6800",
            "--max-connection-per-server=16",
            "--seed-time=0",
            "--quiet=true",
            "--follow-torrent=mem"
        ]
        
        limit = self.config.get("download_limit")
        if limit > 0:
            cmd.append(f"--max-download-limit={limit}K")

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        self.aria2_process = subprocess.Popen(
            cmd, 
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(1)
        
        try:
            self.rpc = xmlrpc.client.ServerProxy("http://localhost:6800/rpc")
            self.rpc.aria2.getVersion()
        except: pass

    def add_magnet(self, magnet_link, save_path):
        if not self.rpc: return None
        try:
            options = {"dir": save_path}
            gid = self.rpc.aria2.addUri([magnet_link], options)
            return gid
        except: return None

    def pause_torrent(self, gid):
        if self.rpc: self.rpc.aria2.pause(gid)

    def resume_torrent(self, gid):
        if self.rpc: self.rpc.aria2.unpause(gid)

    def remove_torrent(self, gid, delete_files=False):
        if not self.rpc: return
        try:
            self.rpc.aria2.remove(gid)
        except:
            try: self.rpc.aria2.removeDownloadResult(gid)
            except: pass

    def clear_finished(self):
        """Löscht fertige Downloads aus der Liste"""
        if not self.rpc: return
        with self.lock:
            current_gids = list(self.torrents.keys())
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

    def _monitor_loop(self):
        # Felder die wir von Aria2 abfragen (jetzt inklusive 'followedBy')
        keys = ["gid", "status", "totalLength", "completedLength", 
                "downloadSpeed", "dir", "bittorrent", "followedBy"]
        
        while self.running:
            if not self.rpc: 
                time.sleep(1)
                continue
                
            try:
                active = self.rpc.aria2.tellActive(keys)
                waiting = self.rpc.aria2.tellWaiting(0, 100, keys)
                stopped = self.rpc.aria2.tellStopped(0, 100, keys)
                
                all_downloads = active + waiting + stopped
                current_torrents = {}
                
                for d in all_downloads:
                    gid = d['gid']
                    status_raw = d['status']
                    
                    # === FILTER LOGIK ===
                    # Wenn der Download fertig ist UND es nur Metadaten waren
                    # (Erkennbar daran, dass er einen Nachfolger 'followedBy' hat 
                    #  oder der Name immer noch der Placeholder ist)
                    
                    is_metadata_artifact = False
                    
                    # Check 1: Hat es einen Nachfolger? (Dann war dies nur der .torrent Download)
                    if 'followedBy' in d:
                        is_metadata_artifact = True
                        
                    # Name ermitteln
                    name = "Unbekannt / Metadata"
                    if 'bittorrent' in d and 'info' in d['bittorrent']:
                        name = d['bittorrent']['info'].get('name', name)
                    
                    # Check 2: Ist fertig, heißt aber immer noch Metadata (Backup Check)
                    if status_raw == 'complete' and name == "Unbekannt / Metadata":
                        is_metadata_artifact = True

                    # Wenn es ein Artefakt ist -> Aus Aria2 löschen & überspringen
                    if status_raw == 'complete' and is_metadata_artifact:
                        try:
                            self.rpc.aria2.removeDownloadResult(gid)
                        except: pass
                        continue 
                    # ====================
                    
                    # Normale Verarbeitung
                    total = int(d['totalLength'])
                    done = int(d['completedLength'])
                    speed = int(d['downloadSpeed'])
                    
                    progress = 0.0
                    if total > 0:
                        progress = (done / total) * 100
                    
                    state_str = status_raw.capitalize()
                    
                    # Wenn aktiv aber noch keine Größe -> Metadaten laden
                    if status_raw == 'active' and total == 0:
                        state_str = "Metadata"
                    elif status_raw == 'active':
                        state_str = "Downloading"
                    
                    eta = 0
                    if speed > 0 and total > done:
                        eta = int((total - done) / speed)
                        
                    current_torrents[gid] = TorrentData(
                        gid=gid,
                        name=name,
                        progress=progress,
                        state_str=state_str,
                        download_speed=speed,
                        eta=eta,
                        save_path=d['dir'],
                        total_size=total
                    )
                    
                    # Auto Open Logik
                    if status_raw == "complete" and self.config.get("auto_open_on_finish"):
                         # Einfacher Schutz gegen mehrfaches Öffnen nötig
                         pass

                with self.lock:
                    self.torrents = current_torrents
                    
            except Exception as e:
                pass
            
            time.sleep(1)

    def get_all_torrents(self):
        with self.lock:
            return self.torrents.copy()

    def open_folder(self, path):
        try:
            if os.name == 'nt': os.startfile(path)
            else: subprocess.run(["xdg-open", path])
        except: pass

    def shutdown(self):
        self.running = False
        if self.aria2_process:
            self.aria2_process.terminate()