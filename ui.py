import os
import msvcrt  # WICHTIG: Nur auf Windows verfügbar (hast du ja)
import time
import sys

class UI:
    def __init__(self):
        self.width = 70

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def header(self):
        self.clear()
        print("+" + "=" * (self.width - 2) + "+")
        print("|" + "osTorrent (Aria2 Engine)".center(self.width - 2) + "|")
        print("+" + "=" * (self.width - 2) + "+")
        print()

    def menu(self, title, options):
        self.header()
        print(f"  >> {title}")
        print("-" * self.width)
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        print()
        print(f"  [0] Zurück / Exit")
        print("-" * self.width)

    def input(self, prompt):
        """Standard blockierender Input"""
        try: return input(f"  {prompt}: ").strip()
        except: return "0"

    def wait_for_input(self, timeout=3):
        """
        Wartet 'timeout' Sekunden auf eine Eingabe.
        Gibt den gedrückten Buchstaben zurück oder None bei Timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Prüfen ob eine Taste gedrückt wurde
            if msvcrt.kbhit():
                # Taste lesen (byte) und decodieren
                char = msvcrt.getch()
                try:
                    return char.decode('utf-8').lower()
                except:
                    return '?' # Falls Sondertaste
            time.sleep(0.1)
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
        if t.state_str == "Downloading": icon = "[DL]"
        elif t.state_str == "Complete": icon = "[OK]"
        elif t.state_str == "Paused": icon = "[||]"
        elif t.state_str == "Metadata": icon = "[META]"
        elif t.state_str == "Removed": icon = "[X]"

        print(f"  [{idx}] {icon} {t.name}")
        print(f"      {bar} ({t.progress:.1f}%)")
        if t.state_str in ["Downloading", "Metadata"]:
            print(f"      {speed_str} | ETA: {eta_str} | {t.state_str}")
        else:
            print(f"      Status: {t.state_str}")
        print()

    def message(self, msg):
        print(f"\n  {msg}")
        input("  [Enter]...")