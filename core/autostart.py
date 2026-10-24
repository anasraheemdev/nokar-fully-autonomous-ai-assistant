"""
core/autostart.py — Windows, macOS, and Linux Startup Manager for Nokar.

Ensures Nokar opens automatically as a startup app upon laptop boot/login,
with working directory set to project root and single-instance safety.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

_OS = platform.system()


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
SCRIPT_PATH = BASE_DIR / "main.py"
ICON_PATH = BASE_DIR / "config" / "jarvis.ico"


def get_pythonw_executable() -> str:
    """Return pythonw.exe if available to run without console window, else sys.executable."""
    if _OS == "Windows":
        pythonw = Path(sys.executable).parent / "pythonw.exe"
        if pythonw.exists():
            return str(pythonw)
    return sys.executable


def get_windows_startup_shortcut_path() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "Nokar.lnk"


def is_autostart_enabled() -> bool:
    """Check if Nokar is registered to run on startup."""
    if _OS == "Windows":
        # 1. Check Registry Run key
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            for name in ("Nokar", "JARVIS_AI"):
                try:
                    winreg.QueryValueEx(key, name)
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

        # 2. Check Startup folder shortcut
        try:
            shortcut = get_windows_startup_shortcut_path()
            if shortcut.exists():
                return True
        except Exception:
            pass

        return False

    elif _OS == "Darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.nokar.assistant.plist"
        old_plist = Path.home() / "Library" / "LaunchAgents" / "com.jarvis.assistant.plist"
        return plist.exists() or old_plist.exists()

    else:
        desk = Path.home() / ".config" / "autostart" / "nokar.desktop"
        old_desk = Path.home() / ".config" / "autostart" / "jarvis.desktop"
        return desk.exists() or old_desk.exists()


def enable_autostart() -> tuple[bool, str]:
    """Register Nokar to launch automatically upon user login."""
    exe = get_pythonw_executable()
    script = str(SCRIPT_PATH)
    base = str(BASE_DIR)

    if _OS == "Windows":
        msg_parts = []
        # 1. Register in Windows Registry Run key
        try:
            import winreg
            reg = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS
            )
            winreg.SetValueEx(reg, "Nokar", 0, winreg.REG_SZ, f'"{exe}" "{script}"')
            winreg.CloseKey(reg)
            msg_parts.append("Registry Run key set")
        except Exception as e:
            msg_parts.append(f"Registry error: {e}")

        # 2. Create Startup folder shortcut
        try:
            shortcut_path = get_windows_startup_shortcut_path()
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(shortcut_path))
            shortcut.TargetPath = exe
            shortcut.Arguments = f'"{script}"'
            shortcut.WorkingDirectory = base
            shortcut.Description = "Nokar AI Desktop Assistant"
            if ICON_PATH.exists():
                shortcut.IconLocation = str(ICON_PATH)
            shortcut.Save()
            msg_parts.append("Startup folder shortcut created")
        except Exception as e:
            msg_parts.append(f"Shortcut error: {e}")

        return True, " | ".join(msg_parts)

    elif _OS == "Darwin":
        try:
            plist_dir = Path.home() / "Library" / "LaunchAgents"
            plist_dir.mkdir(parents=True, exist_ok=True)
            plist = plist_dir / "com.nokar.assistant.plist"
            plist.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0"><dict>\n'
                '  <key>Label</key><string>com.nokar.assistant</string>\n'
                '  <key>ProgramArguments</key><array>\n'
                f'    <string>{exe}</string>\n'
                f'    <string>{script}</string>\n'
                '  </array>\n'
                f'  <key>WorkingDirectory</key><string>{base}</string>\n'
                '  <key>RunAtLoad</key><true/>\n'
                '</dict></plist>\n',
                encoding="utf-8"
            )
            return True, "macOS LaunchAgent created"
        except Exception as e:
            return False, f"macOS autostart error: {e}"

    else:
        try:
            desk_dir = Path.home() / ".config" / "autostart"
            desk_dir.mkdir(parents=True, exist_ok=True)
            desk = desk_dir / "nokar.desktop"
            desk.write_text(
                "[Desktop Entry]\n"
                "Name=Nokar\n"
                f"Exec={exe} {script}\n"
                f"Path={base}\n"
                "Type=Application\nTerminal=false\n"
                "X-GNOME-Autostart-enabled=true\n",
                encoding="utf-8"
            )
            return True, "Linux autostart entry created"
        except Exception as e:
            return False, f"Linux autostart error: {e}"


def disable_autostart() -> tuple[bool, str]:
    """Unregister Nokar from startup."""
    if _OS == "Windows":
        # 1. Remove from Registry
        try:
            import winreg
            reg = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS
            )
            for name in ("Nokar", "JARVIS_AI"):
                try:
                    winreg.DeleteValue(reg, name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(reg)
        except Exception:
            pass

        # 2. Remove from Startup folder
        try:
            shortcut = get_windows_startup_shortcut_path()
            if shortcut.exists():
                shortcut.unlink(missing_ok=True)
        except Exception:
            pass

        return True, "Removed from Windows autostart"

    elif _OS == "Darwin":
        for name in ("com.nokar.assistant.plist", "com.jarvis.assistant.plist"):
            p = Path.home() / "Library" / "LaunchAgents" / name
            p.unlink(missing_ok=True)
        return True, "Removed from macOS LaunchAgents"

    else:
        for name in ("nokar.desktop", "jarvis.desktop"):
            p = Path.home() / ".config" / "autostart" / name
            p.unlink(missing_ok=True)
        return True, "Removed from Linux autostart"
