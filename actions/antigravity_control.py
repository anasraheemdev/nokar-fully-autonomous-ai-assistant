"""
actions/antigravity_control.py — Autonomous Antigravity IDE & Agent Integration.

Capabilities:
  • Autonomously launch Google Antigravity into any folder, workspace, or drive.
  • Intelligently refine the user's brief voice/text instructions into an expert,
    production-grade engineering prompt using JARVIS's Gemini SMART reasoning tier.
  • Launch Antigravity in full agent mode (`antigravity-ide chat -m agent "<prompt>"`)
    to execute multi-step software engineering tasks autonomously.
  • Execute with Administrator/Elevated privileges (Windows UAC `RunAs`) when requested.
  • Query running Antigravity sessions and status.
  • Auto-discovered at startup by core.action_loader.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

_OS = platform.system()
BASE_DIR = Path(__file__).resolve().parent.parent

_CNW: dict = (
    {"creationflags": subprocess.CREATE_NO_WINDOW}
    if _OS == "Windows" else {}
)

# Known executable candidates for Antigravity IDE
_CANDIDATE_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Antigravity IDE" / "bin" / "antigravity-ide.cmd",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Antigravity IDE" / "Antigravity IDE.exe",
    Path(os.environ.get("PROGRAMFILES", "")) / "Antigravity IDE" / "bin" / "antigravity-ide.cmd",
]


def _find_antigravity_bin() -> str:
    """Locate the antigravity CLI or executable."""
    # 1. System PATH
    found = shutil.which("antigravity-ide.cmd") or shutil.which("antigravity-ide") or shutil.which("antigravity")
    if found:
        return found
    # 2. Known Windows paths
    for cand in _CANDIDATE_PATHS:
        if cand.exists():
            return str(cand)
    return "antigravity-ide.cmd"


def _resolve_target_folder(raw: str) -> Path:
    """Resolve a target folder with fuzzy project resolution."""
    raw = str(raw or "").strip().strip('"').strip("'")
    if not raw or raw.lower() in (".", "current", "workspace", "jarvis", "here"):
        return BASE_DIR

    from actions.file_controller import _resolve_path, _smart_find_file

    target = _resolve_path(raw)
    if target.exists() and target.is_dir():
        return target

    # Search in Desktop, Documents, OneDrive, and root drives
    found = _smart_find_file(raw)
    if found:
        return found if found.is_dir() else found.parent

    # Try matching directory names in user directories
    for parent in [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "OneDrive", BASE_DIR.parent]:
        if parent.exists():
            try:
                for d in parent.iterdir():
                    if d.is_dir() and raw.lower() in d.name.lower():
                        return d
            except Exception:
                continue

    return target if target.exists() else BASE_DIR


def _refine_prompt_with_gemini(raw_prompt: str, folder: Path) -> str:
    """Transform user prompt into an expert engineering prompt for Antigravity."""
    try:
        from core import gemini

        # Inventory context of folder
        file_list = []
        try:
            for item in sorted(folder.iterdir())[:25]:
                file_list.append(f"- {item.name}{'/' if item.is_dir() else ''}")
        except Exception:
            pass
        folder_ctx = "\n".join(file_list) if file_list else "(Directory contents unlisted)"

        instruction = (
            f"You are JARVIS's Chief Software Architect. The user wants the coding agent Antigravity "
            f"to perform a coding task in the workspace: '{folder.name}' ({folder}).\n\n"
            f"Workspace top-level files:\n{folder_ctx}\n\n"
            f"User request: \"{raw_prompt}\"\n\n"
            f"Task: Rewrite and expand this request into a high-precision, technical, and complete "
            f"engineering specification for Antigravity's agent mode. Include:\n"
            f"• Objective & Acceptance Criteria\n"
            f"• Key Files and Architecture to Inspect\n"
            f"• Step-by-Step Implementation Instructions\n"
            f"• Verification and Testing Requirements\n\n"
            f"Output ONLY the final prompt text without meta-commentary, greetings, or conversational filler."
        )

        resp = gemini.call(instruction, tier=gemini.SMART, timeout_ms=30000)
        if resp and isinstance(resp, str) and len(resp.strip()) > 30:
            return resp.strip()
    except Exception as e:
        print(f"[antigravity] Prompt refinement fallback: {e}")

    # Fallback template
    return (
        f"# Goal: {raw_prompt}\n\n"
        f"Workspace: {folder}\n"
        f"Please analyze the codebase in this directory, implement the requested functionality thoroughly, "
        f"test your changes, and ensure high code quality."
    )


# ── Core Operations ──────────────────────────────────────────────────────────

def open_workspace(folder: str = "") -> str:
    """Open Antigravity IDE into the target folder."""
    target_dir = _resolve_target_folder(folder)
    bin_path = _find_antigravity_bin()

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([bin_path, str(target_dir)], **_CNW)
        return f"Opened Antigravity IDE in: {target_dir.name} ({target_dir})"
    except Exception as e:
        return f"Could not launch Antigravity IDE: {e}"


def run_agent_task(
    prompt: str,
    folder: str = "",
    mode: str = "agent",
    admin: bool = False,
    refine: bool = True,
    player=None,
) -> str:
    """Refine prompt and execute Antigravity in agent mode."""
    if not prompt or not prompt.strip():
        return "Please provide a task or prompt for Antigravity to work on."

    target_dir = _resolve_target_folder(folder)
    target_dir.mkdir(parents=True, exist_ok=True)
    bin_path = _find_antigravity_bin()

    if player:
        player.write_log(f"[antigravity] Refining task for {target_dir.name}...")

    # Refine prompt if requested
    final_prompt = _refine_prompt_with_gemini(prompt, target_dir) if refine else prompt.strip()

    if player:
        player.write_log(f"[antigravity] Refined prompt: {final_prompt[:150]}...")

    try:
        if admin and _OS == "Windows":
            # Launch elevated via PowerShell Start-Process with -Verb RunAs
            # Write prompt to a temporary file to avoid shell quoting issues
            temp_prompt = target_dir / ".antigravity_task.txt"
            temp_prompt.write_text(final_prompt, encoding="utf-8")

            ps_cmd = (
                f"$p = Get-Content -Raw -Path '{temp_prompt}'; "
                f"Start-Process -FilePath '{bin_path}' -ArgumentList @('chat', '-m', '{mode}', $p) "
                f"-WorkingDirectory '{target_dir}' -Verb RunAs"
            )
            subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", ps_cmd], **_CNW)
            return (
                f"Launched Antigravity in Administrator mode for '{target_dir.name}'. "
                f"Antigravity agent is now executing your task."
            )
        else:
            # Standard launch
            cmd = [bin_path, "chat", "-m", mode, final_prompt]
            subprocess.Popen(cmd, cwd=str(target_dir), **_CNW)
            return (
                f"Antigravity agent launched in '{target_dir.name}' ({mode} mode). "
                f"Task initialized with refined engineering specifications."
            )
    except Exception as e:
        return f"Failed to start Antigravity agent: {e}"


def check_status() -> str:
    """Check running Antigravity IDE processes."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                pname = p.info["name"].lower()
                if "antigravity" in pname:
                    procs.append(f"PID {p.info['pid']} ({p.info['name']})")
            except Exception:
                continue
        if procs:
            return f"Antigravity is active ({len(procs)} process(es)):\n" + "\n".join(procs)
        return "No running Antigravity processes detected."
    except Exception as e:
        return f"Could not check process status: {e}"


# ── Action Dispatcher ────────────────────────────────────────────────────────

def antigravity_control(parameters: dict = None, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = params.get("action", "agent_task").lower().strip()
    folder = params.get("folder", "")
    prompt = params.get("prompt", "")
    mode = params.get("mode", "agent").lower().strip()
    admin = bool(params.get("admin", False))
    refine = bool(params.get("refine", True))

    if player:
        player.write_log(f"[antigravity] {action} (folder: {folder or 'current'}, admin: {admin})")

    if action in ("agent_task", "run", "start_agent", "chat"):
        return run_agent_task(
            prompt=prompt,
            folder=folder,
            mode=mode,
            admin=admin,
            refine=refine,
            player=player,
        )
    elif action in ("open", "open_workspace", "launch"):
        return open_workspace(folder=folder)
    elif action == "status":
        return check_status()
    else:
        return f"Unknown antigravity action: '{action}'. Available: agent_task | open | status"


# ── Tool Declaration (auto-discovered by core/action_loader.py) ──────────────
TOOL = {
    "name": "antigravity_control",
    "description": (
        "Controls Google Antigravity IDE and coding agent: "
        "launches Antigravity into any folder, refines user requests into comprehensive "
        "engineering specifications using Gemini SMART reasoning, triggers Antigravity agent mode "
        "to autonomously build/fix code, supports Administrator/elevated execution, and inspects status. "
        "Use this whenever the user wants to start Antigravity, delegate coding tasks to Antigravity, "
        "or open projects in Antigravity."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "agent_task | open | status (default: agent_task)"
            },
            "prompt": {
                "type": "STRING",
                "description": "The coding task, feature request, or bug fix for Antigravity to solve"
            },
            "folder": {
                "type": "STRING",
                "description": "Target repository or folder (e.g. current, jarvis, desktop, D:/projects/app, or project name)"
            },
            "admin": {
                "type": "BOOLEAN",
                "description": "Set to true to launch with elevated Administrator privileges"
            },
            "mode": {
                "type": "STRING",
                "description": "Antigravity chat mode: agent (default) | edit | ask"
            },
            "refine": {
                "type": "BOOLEAN",
                "description": "True (default) to refine prompt into an expert technical specification before launch"
            }
        },
        "required": ["prompt"]
    },
    "handler": antigravity_control,
}
