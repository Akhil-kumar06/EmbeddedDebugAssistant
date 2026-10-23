"""Fixed build action; AI cannot call it. GUI requests user confirmation."""
import os,subprocess,sys
from pathlib import Path
def run_build(folder):
    folder=Path(folder).resolve()
    if not (folder/'build.py').is_file():raise ValueError('Choose the project folder containing build.py.')
    if os.name=='nt':
        converted=subprocess.run(['wsl.exe','-d','Ubuntu','--','wslpath','-a',str(folder)],
                    capture_output=True,text=True,timeout=15,check=True).stdout.strip()
        if not converted.startswith('/'):raise ValueError('WSL path conversion failed.')
        command=['wsl.exe','-d','Ubuntu','--cd',converted,'--','timeout','60s','python3','build.py'];cwd=None
    else:
        command=['timeout','60s',sys.executable,'build.py'];cwd=folder
    p=subprocess.run(command,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,errors='replace',timeout=75)
    return f'Project: {folder}\nExit code: {p.returncode}\n\n'+p.stdout[-12000:]
