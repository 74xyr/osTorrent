import os
import msvcrt
import time
import sys

class UI:
    def __init__(self):
        self.width = 70
        # ANSI Escape Codes für Hellblau (Cyan ist meist besser lesbar als Dunkelblau)
        self.COLOR = "\033[96m" 
        self.RESET = "\033[0m"

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def header(self):
        self.clear()
        # Header in Hellblau
        print(self.COLOR + "+" + "=" * (self.width - 2) + "+")
        # Nur noch "osTorrent"
        print("|" + "osTorrent".center(self.width - 2) + "|")
        print("+" + "=" * (self.width - 2) + "+" + self.RESET)
        print()

    def menu(self, title, options):
        self.header()
        print(self.COLOR + f"  >> {title}" + self.RESET)
        print("-" * self.width)
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        print()
        print(f"  [0] Zurück / Exit")
        print("-" * self.width)

    def input(self, prompt):
        try: 
            # Input Prompt auch leicht einfärben
            return input(self.COLOR + f"  {prompt}: " + self.RESET).strip()
        except: return "0"

    def wait_for_input(self, timeout=3):
        """Wartet auf Tastendruck oder Timeout"""
        # Wenn Timeout 0 ist (durchgehend), warten wir trotzdem kurz (0.1s),
        # damit die CPU nicht explodiert und man Zeit hat zu drücken.
        if timeout <= 0:
            timeout = 0.1
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if msvcrt.kbhit():
                try:
                    return msvcrt.getch().decode('utf-8').lower()
                except:
                    return '?'
            time.sleep(0.05)
        return None

    def print_torrent(self, idx, t):
        bar_len = 20
        filled = int(bar_len * t.progress / 100)
        bar = "+" * filled + "-" * (bar_len - filled)
        
        speed = t.download_speed / 1024
        speed_str = f"{speed:.1f} KB/s"
        if speed > 1024: speed_str = f"{speed/1024:.1f} MB/s"
        
        eta_str = "∞"
        if t.eta > 0:
            m, s = divmod(t.eta, 60)
            h, m = divmod(m, 60)
            eta_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"

        icon = "[?]"
        # Icons und Status etwas cleaner
        if t.state_str == "Downloading": icon = "[DL]"
        elif t.state_str == "Complete": icon = "[OK]"
        elif t.state_str == "Paused": icon = "[||]"
        elif t.state_str == "Metadata": icon = "[META]"
        elif t.state_str == "Removed": icon = "[X]"

        # Textausgabe (Hellblau nur für den Namen)
        print(f"  [{idx}] {icon} {self.COLOR}{t.name}{self.RESET}")
        print(f"      {bar} ({t.progress:.1f}%)")
        
        status_line = ""
        if t.state_str in ["Downloading", "Metadata"]:
            status_line = f"{speed_str} | ETA: {eta_str}"
        else:
            status_line = f"Status: {t.state_str}"
            
        print(f"      {status_line}")
        print()

    def message(self, msg):
        print(self.COLOR + f"\n  {msg}" + self.RESET)
        input("  [Enter]...")