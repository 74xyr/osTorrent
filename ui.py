import os
import msvcrt
import sys

class UI:
    def __init__(self):
        self.width = 75
        self.CYAN = "\033[96m" 
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.RESET = "\033[0m"
        
        # Aktiviert ANSI Colors in Windows CMD
        os.system('')

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def header(self, title="osTorrent"):
        self.clear()
        print(self.CYAN + "+" + "=" * (self.width - 2) + "+")
        print("|" + title.center(self.width - 2) + "|")
        print("+" + "=" * (self.width - 2) + "+" + self.RESET)
        print()

    def get_key(self):
        """Liest einen einzelnen Tastendruck (blockierend)"""
        key = msvcrt.getch()
        if key == b'\xe0': # Pfeiltasten senden erst e0
            key = msvcrt.getch()
            if key == b'H': return 'up'
            if key == b'P': return 'down'
            if key == b'K': return 'left'
            if key == b'M': return 'right'
        if key == b'\r': return 'enter'
        try: return key.decode('utf-8').lower()
        except: return None

    def select_menu(self, title, options, exit_option=True):
        """Zeigt ein Menü mit Pfeiltasten-Navigation"""
        selected = 0
        while True:
            self.header(title)
            
            for i, option in enumerate(options):
                prefix = "  "
                color = self.RESET
                if i == selected:
                    prefix = "> "
                    color = self.CYAN
                
                print(f"{color}{prefix}{option}{self.RESET}")
            
            if exit_option:
                print()
                prefix = "  "
                color = self.RESET
                if selected == len(options):
                    prefix = "> "
                    color = self.RED
                print(f"{color}{prefix}[ Zurück / Exit ]{self.RESET}")

            # Input Handling
            key = self.get_key()
            if key == 'up':
                selected = max(0, selected - 1)
            elif key == 'down':
                limit = len(options) if exit_option else len(options) - 1
                selected = min(limit, selected + 1)
            elif key == 'enter':
                if exit_option and selected == len(options):
                    return -1
                return selected

    def print_torrent(self, idx, t):
        bar_len = 25
        filled = int(bar_len * t.progress / 100)
        bar = "+" * filled + "-" * (bar_len - filled)
        
        speed_str = f"{t.download_speed/1024:.1f} KB/s"
        if t.download_speed > 1024: speed_str = f"{t.download_speed/1048576:.1f} MB/s"
        
        eta_str = "∞"
        if t.eta > 0:
            m, s = divmod(t.eta, 60)
            h, m = divmod(m, 60)
            eta_str = f"{h}h {m}m"

        icon = "[?]"
        color = self.RESET
        if t.state_str == "Downloading": 
            icon = "[DL]"
            color = self.GREEN
        elif t.state_str == "Complete": 
            icon = "[OK]"
            color = self.CYAN
        elif t.state_str == "Paused": 
            icon = "[||]"
            color = self.YELLOW

        print(f"  {color}{icon} {t.name}{self.RESET}")
        print(f"      {bar} ({t.progress:.1f}%)")
        
        if t.state_str in ["Downloading", "Metadata"]:
            print(f"      {speed_str} | ETA: {eta_str}")
        else:
            print(f"      Status: {t.state_str}")
        print()

    def message(self, msg, color=""):
        print(f"{color}  {msg}{self.RESET}")
        print("  Drücke eine Taste...")
        msvcrt.getch()

    def confirm(self, question):
        """Fragt J/N ab (ohne Enter)"""
        print(f"\n  {self.YELLOW}{question} (J/N){self.RESET}")
        while True:
            key = self.get_key()
            if key == 'j' or key == 'y': return True
            if key == 'n': return False