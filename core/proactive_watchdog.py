"""
core/proactive_watchdog.py — Autonomous Executive Assistant & System Guardian.

Capabilities:
  • Periodic Inbox Monitoring: Autonomously checks configured SMTP/POP/IMAP email
    for new messages and alerts the user.
  • System Resource Guardian: Monitors CPU, RAM, and GPU for critical load spikes.
  • Project Milestone Tracker: Inspects ongoing project progress in memory/ongoing_projects.json.
  • Dispatches non-blocking notifications to the NOKAR UI and audio channel.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import psutil

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROJECTS_PATH = BASE_DIR / "memory" / "ongoing_projects.json"


class ProactiveWatchdog:
    """Autonomous executive background watchdog."""

    def __init__(
        self,
        notify_fn: Optional[Callable[[str], None]] = None,
        say_fn: Optional[Callable[[str], None]] = None,
        check_interval_sec: int = 60,
    ):
        self._notify = notify_fn or (lambda msg: print(f"[Watchdog] {msg}"))
        self._say = say_fn
        self._interval = max(15, check_interval_sec)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._seen_mail_subjects: set[str] = set()
        self._last_mail_check = 0.0
        self._last_sys_alert = 0.0
        self._last_project_check = 0.0
        self._high_load_count = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ProactiveWatchdog")
        self._thread.start()
        print("[Watchdog] Proactive Executive Watchdog active.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        print("[Watchdog] Proactive Executive Watchdog stopped.")

    def _run_loop(self) -> None:
        # Initial brief warm-up delay before first check
        time.sleep(10.0)

        while not self._stop_event.is_set():
            try:
                now = time.monotonic()

                # 1. System Resource Guardian (every 30 seconds)
                self._check_system_health(now)

                # 2. Email Inbox Watchdog (every 180 seconds)
                if now - self._last_mail_check >= 180.0:
                    self._check_inbox(now)

                # 3. Ongoing Projects Tracker (every 25 minutes)
                if now - self._last_project_check >= 1500.0:
                    self._check_projects(now)

            except Exception as e:
                print(f"[Watchdog] ⚠️ Error in watchdog loop: {e}")

            # Sleep in small increments for responsive shutdown
            for _ in range(self._interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

    def _check_system_health(self, now: float) -> None:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        if cpu > 90.0 or mem > 90.0:
            self._high_load_count += 1
            if self._high_load_count >= 2 and (now - self._last_sys_alert >= 600.0):
                self._last_sys_alert = now
                self._high_load_count = 0
                msg = f"SYS: [System Alert] ⚠️ High system load: CPU {cpu:.1f}%, RAM {mem:.1f}%."
                self._notify(msg)
        else:
            self._high_load_count = 0

    def _check_inbox(self, now: float) -> None:
        self._last_mail_check = now
        try:
            from actions.email_manager import _load_config, _get_provider_config, read_emails_pop, read_emails_imap

            email_cfg = _load_config()
            if not email_cfg or not email_cfg.get("address") or not email_cfg.get("password"):
                return

            pcfg = _get_provider_config(email_cfg.get("address", ""), email_cfg)

            # Try IMAP first, fallback to POP
            res = ""
            if pcfg.get("imap_host"):
                res = read_emails_imap(email_cfg, pcfg, max_count=3, unread_only=True)
            elif pcfg.get("pop_host"):
                res = read_emails_pop(email_cfg, pcfg, max_count=3)

            if res and "No unread" not in res and "Failed" not in res and "Authentication failed" not in res:
                # Extract first subject line if present
                for line in res.split("\n"):
                    if "Subject:" in line:
                        sub = line.split("Subject:", 1)[-1].strip()
                        if sub and sub not in self._seen_mail_subjects:
                            self._seen_mail_subjects.add(sub)
                            alert = f"SYS: [Inbox Watchdog] ✉ New Email: '{sub}'"
                            self._notify(alert)
                            if self._say:
                                self._say(f"Anas, you have received a new email regarding: {sub}")
                            break
        except Exception:
            pass

    def _check_projects(self, now: float) -> None:
        self._last_project_check = now
        if not PROJECTS_PATH.exists():
            return
        try:
            data = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
            ongoing = data.get("ongoing_projects", [])
            if ongoing and isinstance(ongoing, list):
                proj = ongoing[0]
                pname = proj.get("name", "Active Project")
                pstatus = proj.get("status", "in progress")
                self._notify(f"SYS: [Project Tracker] 📁 Milestone focus: '{pname}' ({pstatus}).")
        except Exception:
            pass


# Singleton instance
_watchdog: Optional[ProactiveWatchdog] = None


def get_watchdog(notify_fn=None, say_fn=None) -> ProactiveWatchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = ProactiveWatchdog(notify_fn=notify_fn, say_fn=say_fn)
    return _watchdog
