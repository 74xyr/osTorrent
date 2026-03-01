import os
import msvcrt
import sys
import time
import ctypes

class UI:
    def __init__(self):
        self.width = 75
        self.CYAN = "\033[96m" 
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.RESET = "\033[0m"
        
        self._enable_windows_10_ansi()
        self.set_title('osTorrent') # Standard Titel beim Start
        self._set_icon()

        self.art = {
            "main": r"""
             ___________                                 __   
  ____  _____\__    ___/_________________   ____   _____/  |_ 
 /  _ \/  ___/ |    | /  _ \_  __ \_  __ \_/ __ \ /    \   __\
(  <_> )___ \  |    |(  <_> )  | \/|  | \/\  ___/|   |  \  |  
 \____/____  > |____| \____/|__|   |__|    \___  >___|  /__|  
           \/                                  \/     \/      
""",
            "loading": r"""
.____                     .___.__                           
|    |    _________     __| _/|__| ____    ____             
|    |   /  _ \__  \   / __ | |  |/    \  / ___\            
|    |__(  <_> ) __ \_/ /_/ | |  |   |  \/ /_/  >           
|_______ \____(____  /\____ | |__|___|  /\___  / /\  /\  /\ 
        \/         \/      \/         \//_____/  \/  \/  \/ 
""",
            "settings": r"""
  _________       __    __  .__                      
 /   _____/ _____/  |__/  |_|__| ____    ____  ______
 \_____  \_/ __ \   __\   __\  |/    \  / ___\/  ___/
 /        \  ___/|  |  |  | |  |   |  \/ /_/  >___ \ 
/_______  /\___  >__|  |__| |__|___|  /\___  /____  >
        \/     \/                   \//_____/     \/ 
""",
            "dl_list": r"""
________                      .__                    .___ .____    .__          __   
\______ \   ______  _  ______ |  |   _________     __| _/ |    |   |__| _______/  |_ 
 |    |  \ /  _ \ \/ \/ /    \|  |  /  _ \__  \   / __ |  |    |   |  |/  ___/\   __\
 |    `   (  <_> )     /   |  \  |_(  <_> ) __ \_/ /_/ |  |    |___|  |\___ \  |  |  
/_______  /\____/ \/\_/|___|  /____/\____(____  /\____ |  |_______ \__/____  > |__|  
        \/                  \/                \/      \/          \/       \/        
""",
            "explore": r"""
___________              .__                        
\_   _____/__  _________ |  |   ___________   ____  
 |    __)_\  \/  /\____ \|  |  /  _ \_  __ \_/ __ \ 
 |        \>    < |  |_> >  |_(  <_> )  | \/\  ___/ 
/_______  /__/\_ \|   __/|____/\____/|__|    \___  >
        \/      \/|__|                           \/ 
"""
        }

    def _enable_windows_10_ansi(self):
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except: os.system('')

    def _set_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("osTorrent.App.1.0")
        except: pass

    def set_title(self, text):
        """Setzt den Fenstertitel ohne Flackern"""
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(text)
        except:
            os.system(f'title {text}')

    def clear(self):
        """Löscht den kompletten Screen (langsam, verursacht Flackern)"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def reset_cursor(self):
        """Setzt Cursor nach oben links (schnell, kein Flackern)"""
        print("\033[H", end="")

    def clear_rest(self):
        """Löscht alles ab dem Cursor bis zum Ende des Screens"""
        print("\033[J", end="")

    def type_text(self, text, speed=0.02, color="", end="\n"):
        print(color, end="")
        for char in text:
            print(char, end="", flush=True)
            time.sleep(speed)
        print(self.RESET, end=end)

    def header(self, title="osTorrent", art_key=None, clear=True):
        if clear: 
            self.clear() # Nur nutzen wenn wirklich neuer Screen nötig
        
        if art_key and art_key in self.art:
            print(self.CYAN + self.art[art_key] + self.RESET)
            if art_key == "main":
                print(f"{self.CYAN}                                       made by acay{self.RESET}\n")
            return

        print(self.CYAN + "+" + "=" * (self.width - 2) + "+")
        print("|" + title.center(self.width - 2) + "|")
        print("+" + "=" * (self.width - 2) + "+" + self.RESET)
        print()

    def input(self, prompt, animate=False):
        try:
            p_text = f"  {prompt}: "
            if animate:
                self.type_text(p_text, speed=0.02, color=self.CYAN, end="")
                return input(self.RESET).strip()
            return input(f"{self.CYAN}{p_text}{self.RESET}").strip()
        except: return ""

    def get_key(self):
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            if key == b'H': return 'up'
            if key == b'P': return 'down'
            if key == b'K': return 'left'
            if key == b'M': return 'right'
        if key == b'\r': return 'enter'
        try: return key.decode('utf-8').lower()
        except: return None

    def wait_for_input(self, timeout):
        start = time.time()
        while time.time() - start < timeout:
            if msvcrt.kbhit(): return self.get_key()
            time.sleep(0.05)
        return None

    def select_menu(self, title, options, exit_text="Back", art_key=None, hint=None, animate_hint=False):
        """Menü mit Flicker-Free Navigation"""
        selected = 0
        first_render = True
        
        self.clear()
        
        while True:
            self.reset_cursor()
            self.header(title, art_key, clear=False)
            
            # Pagination
            max_visible = 10
            start_idx = 0
            end_idx = len(options)
            
            if len(options) > max_visible:
                if selected >= max_visible:
                    start_idx = selected - max_visible + 1
                end_idx = start_idx + max_visible

            if start_idx > 0:
                print(f"  {self.YELLOW}  ^ ... {self.RESET}")

            for i in range(start_idx, end_idx):
                option = options[i]
                prefix, color = "  ", self.RESET
                if i == selected: prefix, color = "> ", self.CYAN
                print(f"{color}{prefix}{option[:65]:<65}{self.RESET}")
            
            if end_idx < len(options):
                print(f"  {self.YELLOW}  v ... {self.RESET}")
            
            print()
            prefix, color = "  ", self.RESET
            if selected == len(options): prefix, color = "> ", self.RED
            print(f"{color}{prefix}[ {exit_text} ]{self.RESET}")

            if hint:
                print()
                if animate_hint and first_render:
                    self.type_text(f"  {hint}", color=self.CYAN, speed=0.03)
                else:
                    print(f"  {self.CYAN}{hint}{self.RESET}")

            self.clear_rest()

            first_render = False
            key = self.get_key()
            
            if key == 'up': selected = max(0, selected - 1)
            elif key == 'down': 
                limit = len(options) if exit_text else len(options) - 1
                selected = min(limit, selected + 1)
            elif key == 'enter':
                if exit_text and selected == len(options): return -1
                return selected

    def print_torrent(self, idx, t):
        bar_len = 25
        filled = int(bar_len * t.progress / 100)
        filled = max(0, min(bar_len, filled))
        bar = "+" * filled + "-" * (bar_len - filled)
        
        speed_str = f"{t.download_speed/1024:.1f} KB/s"
        if t.download_speed > 1024: speed_str = f"{t.download_speed/1048576:.1f} MB/s"
        
        eta_str = "Calculating..."
        if t.eta > 0 and t.eta < 31536000:
            m, s = divmod(t.eta, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            if d > 0: eta_str = f"{d}d {h}h"
            elif h > 0: eta_str = f"{h}h {m}m"
            else: eta_str = f"{m}m {s}s"
        elif t.download_speed == 0 and t.state_str == "Downloading":
            eta_str = "∞"
        elif t.progress >= 100 or t.state_str == "Complete":
            eta_str = "Done"

        icon, color = "[?]", self.RESET
        if t.state_str == "Downloading": icon, color = "[DL]", self.GREEN
        elif t.state_str == "Complete": icon, color = "[OK]", self.CYAN
        elif t.state_str == "Paused": icon, color = "[||]", self.YELLOW
        elif t.state_str == "Error": icon, color = "[ER]", self.RED
        elif t.state_str == "Queued": icon, color = "[Q]", self.YELLOW

        name_display = (t.name[:60] + '..') if len(t.name) > 60 else t.name
        print(f"  {color}{icon} {name_display}{self.RESET}")
        
        if t.state_str == "Error":
            print(f"      {self.RED}{t.error_msg}{self.RESET}")
        else:
            print(f"      {bar} ({t.progress:.1f}%)")
            if t.state_str in ["Downloading", "Metadata"]:
                print(f"      {speed_str} | ETA: {eta_str}")
            else:
                print(f"      Status: {t.state_str}")
        print()

    def message(self, msg, color="", animate=True):
        if animate:
            self.type_text(f"  {msg}", color=color)
        else:
            print(f"{color}  {msg}{self.RESET}")
        msvcrt.getch()

    def confirm(self, question, animate=True):
        print()
        if animate:
            self.type_text(f"  {question} (J/N)", color=self.YELLOW, speed=0.03)
        else:
            print(f"  {self.YELLOW}{question} (J/N){self.RESET}")
            
        while True:
            key = self.get_key()
            if key == 'j' or key == 'y': return True
            if key == 'n': return False