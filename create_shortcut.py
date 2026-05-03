import os
import sys
try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    print("Required libraries missing. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "winshell", "pywin32"])
    import winshell
    from win32com.client import Dispatch

def create_shortcut():
    desktop = winshell.desktop()
    path = os.path.join(desktop, "MedAI Pro.lnk")
    target = os.path.join(os.getcwd(), "Launch MedAI.bat")
    wDir = os.getcwd()
    icon = os.path.join(os.getcwd(), "static", "favicon.ico") # Fallback if ico exists

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.Description = "Launch MedAI Healthcare Analytics"
    # If a specific icon is needed, set it here
    # shortcut.IconLocation = icon
    shortcut.save()
    print(f"Shortcut created on Desktop: {path}")

if __name__ == "__main__":
    create_shortcut()
