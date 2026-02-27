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
        
        # === ÄNDERUNG HIER ===
        # Pfad zeigt jetzt auf den "server" Ordner
        self.aria2_path = str(Path(__file__).parent / "server" / "aria2c.exe")
        # =====================
        
        # Starte Aria2c im Hintergrund
        self._start_aria2_daemon()
        
        # Monitor Thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    def clear_finished(self):
            """Loescht alle fertigen oder entfernten Eintraege aus der Liste (RPC Memory)"""
            if not self.rpc: return
            current_gids = list(self.torrents.keys())
            
            for gid in current_gids:
                t = self.torrents[gid]
                if t.state_str in ["Complete", "Error", "Removed"]:
                    try:
                        self.rpc.aria2.removeDownloadResult(gid)
                    except: pass

    def _start_aria2_daemon(self):
        """Startet den Aria2c RPC Server"""
        if not os.path.exists(self.aria2_path):
            print("FEHLER: aria2c.exe nicht gefunden! Bitte in den Projektordner kopieren.")
            return

        # RPC Secret (optional, hier leer für lokal)
        cmd = [
            self.aria2_path,
            "--enable-rpc=true",
            "--rpc-listen-all=false",
            "--rpc-allow-origin-all=true",
            "--rpc-listen-port=6800",
            "--max-connection-per-server=16",
            "--seed-time=0",  # Stoppt Seeding sofort nach Download (optional)
            "--quiet=true"
        ]
        
        # Limit anwenden
        limit = self.config.get("download_limit")
        if limit > 0:
            cmd.append(f"--max-download-limit={limit}K")

        # Prozess starten (versteckt unter Windows)
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
        
        # Kurz warten bis Server da ist
        time.sleep(1)
        
        # Verbindung herstellen
        try:
            self.rpc = xmlrpc.client.ServerProxy("http://localhost:6800/rpc")
            # Test ping
            self.rpc.aria2.getVersion()
        except Exception as e:
            print(f"Konnte nicht zu Aria2 verbinden: {e}")

    def add_magnet(self, magnet_link, save_path):
        """Fügt Download via RPC hinzu"""
        if not self.rpc: return None
        try:
            # Optionen für diesen Download
            options = {
                "dir": save_path
            }
            gid = self.rpc.aria2.addUri([magnet_link], options)
            return gid
        except Exception as e:
            print(f"Add Error: {e}")
            return None

    def pause_torrent(self, gid):
        if self.rpc: self.rpc.aria2.pause(gid)

    def resume_torrent(self, gid):
        if self.rpc: self.rpc.aria2.unpause(gid)

    def remove_torrent(self, gid, delete_files=False):
        if not self.rpc: return
        try:
            self.rpc.aria2.remove(gid)
            # Delete files handling in Aria2 is tricky via RPC remove.
            # Usually users rely on external cleanup or aria2 flags.
            # For now, we just remove from list.
        except:
            # Falls er schon fertig/gestoppt war, nutze removeDownloadResult
            try: self.rpc.aria2.removeDownloadResult(gid)
            except: pass

    def update_limit(self):
        """Setzt globales Limit"""
        if not self.rpc: return
        limit = self.config.get("download_limit")
        limit_str = f"{limit}K" if limit > 0 else "0"
        self.rpc.aria2.changeGlobalOption({"max-download-limit": limit_str})

    def _monitor_loop(self):
        while self.running:
            if not self.rpc: 
                time.sleep(1)
                continue
                
            try:
                # Hole aktive, wartende und gestoppte Downloads
                active = self.rpc.aria2.tellActive(["gid", "status", "totalLength", "completedLength", "downloadSpeed", "dir", "bittorrent"])
                waiting = self.rpc.aria2.tellWaiting(0, 100, ["gid", "status", "totalLength", "completedLength", "downloadSpeed", "dir", "bittorrent"])
                stopped = self.rpc.aria2.tellStopped(0, 100, ["gid", "status", "totalLength", "completedLength", "downloadSpeed", "dir", "bittorrent"])
                
                all_downloads = active + waiting + stopped
                current_torrents = {}
                
                for d in all_downloads:
                    gid = d['gid']
                    
                    # Name bestimmen (bei Magnet erst bekannt nach Metadata)
                    name = "Unbekannt / Metadata"
                    if 'bittorrent' in d and 'info' in d['bittorrent']:
                        name = d['bittorrent']['info'].get('name', name)
                    
                    # Größe & Fortschritt
                    total = int(d['totalLength'])
                    done = int(d['completedLength'])
                    speed = int(d['downloadSpeed'])
                    
                    progress = 0.0
                    if total > 0:
                        progress = (done / total) * 100
                    
                    # Status mapping
                    # aria2 status: active, waiting, paused, error, complete, removed
                    status_raw = d['status']
                    state_str = status_raw.capitalize()
                    
                    if status_raw == 'active' and total == 0:
                        state_str = "Metadata"
                    elif status_raw == 'active':
                        state_str = "Downloading"
                    
                    # ETA
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
                    
                    # Auto Open Check
                    if status_raw == "complete" and self.config.get("auto_open_on_finish"):
                         # Check logic to avoid spamming
                         pass

                with self.lock:
                    self.torrents = current_torrents
                    
            except Exception as e:
                # Verbindung verloren?
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