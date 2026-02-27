import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

def install_aria2():
    base_dir = Path(__file__).parent
    server_dir = base_dir / "server"
    aria2_exe = server_dir / "aria2c.exe"
    
    if aria2_exe.exists(): return True
        
    print("  Installing Aria2c Engine...")
    DOWNLOAD_URL = "https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0-win-64bit-build1.zip"
    ZIP_FILENAME = "aria2.zip"
    
    try:
        server_dir.mkdir(exist_ok=True)
        zip_path = server_dir / ZIP_FILENAME
        urllib.request.urlretrieve(DOWNLOAD_URL, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith("aria2c.exe"):
                    source = zip_ref.open(file)
                    target = open(aria2_exe, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    break
        
        if zip_path.exists(): os.remove(zip_path)
        return True
    except: return False