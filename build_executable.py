import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])

command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--onefile",
    "--windowed",
    "--name",
    "BumpReminder",
    str(ROOT / "bump_reminder.py"),
]
subprocess.check_call(command, cwd=ROOT)
print(f"Executable created in: {DIST}")
