"""
actions/project_vault.py — Ongoing Project Tracking, Safe Archiving, and Proceedings Memory.

Features:
  • Tracks ongoing projects, current status, and last proceedings/milestones.
  • Safe keeping: creates snapshots/backups of project folders to safe storage locations
    (e.g., OneDrive / Safe Vault directory, excluding heavy node_modules/.git).
  • On-demand retrieval: recalls what the last proceedings were, what was done, and what's next.
  • Auto-syncs with Nokar's RAG system so ongoing projects are always in context.
  • Auto-discovered by core.action_loader.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT_DATA_PATH = BASE_DIR / "memory" / "ongoing_projects.json"

# Default safe storage destination for backups
DEFAULT_SAFE_BACKUP_DIR = Path.home() / "OneDrive" / "Nokar_Safe_Vault"
if not DEFAULT_SAFE_BACKUP_DIR.parent.exists():
    DEFAULT_SAFE_BACKUP_DIR = Path.home() / "Nokar_Safe_Vault"


def _load_projects() -> dict:
    if not VAULT_DATA_PATH.exists():
        # Prepopulate with Anas Raheem's core active initiatives
        initial = {
            "obrix_labs": {
                "name": "Obrix Labs",
                "path": str(Path.home() / "OneDrive" / "Desktop" / "obrixlabs"),
                "status": "active",
                "description": "AI agency, Agentic workflows, AI SaaS, and autonomous software delivery.",
                "last_proceedings": "Built and expanded AI client solutions; establishing global client partnerships.",
                "next_steps": "Scale client acquisition, launch new calling agents, and expand developer team.",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "backup_location": str(DEFAULT_SAFE_BACKUP_DIR / "obrix_labs")
            },
            "unilistics": {
                "name": "Unilistics",
                "path": str(Path.home() / "OneDrive" / "Desktop" / "unilistics"),
                "status": "active",
                "description": "AI-powered study abroad platform for university matching and scholarship tracking.",
                "last_proceedings": "Database architecture and UI completed with Next.js, Supabase, and Tailwind CSS.",
                "next_steps": "Complete scholarship scraper integration and live university application tracking pipeline.",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "backup_location": str(DEFAULT_SAFE_BACKUP_DIR / "unilistics")
            },
            "nokar_assistant": {
                "name": "Nokar (Obrix Labs)",
                "path": str(BASE_DIR),
                "status": "active",
                "description": "Autonomous voice AI desktop assistant with 3D holographic avatar, News, Weather, and Antigravity controls.",
                "last_proceedings": "Configured Hostinger SMTP/IMAP email suite, added RAG knowledge base for Anas Raheem, and integrated Antigravity IDE agent.",
                "next_steps": "Expand daily proactive scheduling and integrate calendar voice briefings.",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "backup_location": str(DEFAULT_SAFE_BACKUP_DIR / "nokar_assistant")
            }
        }
        _save_projects(initial)
        return initial

    try:
        return json.loads(VAULT_DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_projects(data: dict) -> None:
    VAULT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DATA_PATH.write_text(json.dumps(data, indent=4), encoding="utf-8")
    try:
        from memory.rag_engine import get_rag
        get_rag().reload()
    except Exception:
        pass


def _ignore_patterns(path, names):
    ignored = set()
    for name in names:
        if name in ("node_modules", ".git", "__pycache__", ".venv", "venv", ".next", "dist", "build"):
            ignored.add(name)
    return ignored


# ── Core Operations ──────────────────────────────────────────────────────────

def list_ongoing_projects() -> str:
    projects = _load_projects()
    if not projects:
        return "Sir, there are currently no ongoing projects recorded in your vault."

    lines = [f"Found {len(projects)} ongoing project(s) in your vault:\n"]
    for pid, p in projects.items():
        name = p.get("name", pid)
        status = p.get("status", "active")
        updated = p.get("last_updated", "N/A")
        proc = p.get("last_proceedings", "None")
        lines.append(f"📁 {name} [{status.upper()}] (Updated: {updated})")
        lines.append(f"   Last Proceedings: {proc}")
        if p.get("next_steps"):
            lines.append(f"   Next Steps: {p.get('next_steps')}")
        lines.append("")

    return "\n".join(lines)


def get_last_proceedings(project_name: str) -> str:
    projects = _load_projects()
    q = project_name.lower().strip()

    matched = None
    for pid, p in projects.items():
        if q == pid.lower() or q in p.get("name", "").lower():
            matched = p
            break

    if not matched:
        # Fuzzy search
        for pid, p in projects.items():
            if any(term in p.get("name", "").lower() for term in q.split()):
                matched = p
                break

    if not matched:
        return f"Sir, I could not find an ongoing project matching '{project_name}'. You can ask me to list ongoing projects to see all of them."

    name = matched.get("name")
    status = matched.get("status", "active")
    updated = matched.get("last_updated", "Recently")
    proceedings = matched.get("last_proceedings", "No proceedings recorded.")
    next_steps = matched.get("next_steps", "None defined.")
    backup = matched.get("backup_location", "None")

    return (
        f"Sir, regarding our ongoing project '{name}' [{status.upper()}]:\n\n"
        f"• Last Proceedings ({updated}):\n  {proceedings}\n\n"
        f"• Next Milestones:\n  {next_steps}\n\n"
        f"• Safe Backup Location:\n  {backup}"
    )


def update_proceedings(
    project_name: str,
    proceedings: str,
    next_steps: str = "",
    status: str = "active",
    folder_path: str = ""
) -> str:
    projects = _load_projects()
    pid = project_name.lower().replace(" ", "_").strip()

    entry = projects.get(pid, {})
    entry["name"] = project_name
    entry["status"] = status
    entry["last_proceedings"] = proceedings.strip()
    if next_steps:
        entry["next_steps"] = next_steps.strip()
    if folder_path:
        entry["path"] = folder_path.strip()
    entry["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    projects[pid] = entry
    _save_projects(projects)

    return f"Sir, proceedings updated for '{project_name}'. I have saved our progress in the vault and indexed it into memory."


def backup_project(project_name: str, custom_destination: str = "") -> str:
    """Make a safe snapshot backup of the project folder."""
    projects = _load_projects()
    q = project_name.lower().strip()

    matched_id = None
    matched = None
    for pid, p in projects.items():
        if q == pid.lower() or q in p.get("name", "").lower():
            matched_id = pid
            matched = p
            break

    src_path_str = matched.get("path") if matched else ""
    if not src_path_str or not Path(src_path_str).exists():
        from actions.file_controller import _smart_find_file
        found = _smart_find_file(project_name)
        if found and found.is_dir():
            src_path_str = str(found)
        else:
            return f"Sir, could not locate the source folder for '{project_name}' to create a backup."

    src_path = Path(src_path_str)
    dest_root = Path(custom_destination) if custom_destination else DEFAULT_SAFE_BACKUP_DIR
    dest_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{src_path.name}_backup_{timestamp}.zip"
    archive_path = dest_root / archive_name

    try:
        # Create lightweight zip archive (ignoring node_modules, .git, venv)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(src_path):
                # Filter out heavy directories in-place
                dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", ".venv", "venv", ".next", "dist", "build")]
                for file in files:
                    full_path = Path(root) / file
                    arcname = full_path.relative_to(src_path)
                    try:
                        zipf.write(full_path, arcname)
                    except Exception:
                        continue

        if matched_id:
            projects[matched_id]["backup_location"] = str(archive_path)
            projects[matched_id]["last_backup"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save_projects(projects)

        size_mb = archive_path.stat().st_size / (1024 * 1024)
        return (
            f"Sir, I have safely backed up '{src_path.name}' ({size_mb:.2f} MB) to safe storage:\n"
            f"📂 {archive_path}"
        )
    except Exception as e:
        return f"Sir, safe backup failed for '{project_name}': {e}"


# ── Action Dispatcher ────────────────────────────────────────────────────────

def project_vault(parameters: dict = None, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = params.get("action", "get_proceedings").lower().strip()
    project_name = params.get("project_name", "")

    if player:
        player.write_log(f"[project_vault] {action} {project_name}")

    if action in ("get_proceedings", "last_proceedings", "status", "proceedings"):
        if not project_name:
            return list_ongoing_projects()
        return get_last_proceedings(project_name)

    elif action in ("list", "list_projects", "all"):
        return list_ongoing_projects()

    elif action in ("update", "save_proceedings", "record"):
        return update_proceedings(
            project_name=project_name,
            proceedings=params.get("proceedings", ""),
            next_steps=params.get("next_steps", ""),
            status=params.get("status", "active"),
            folder_path=params.get("folder_path", ""),
        )

    elif action in ("backup", "safe_keep", "archive"):
        return backup_project(
            project_name=project_name,
            custom_destination=params.get("destination", "")
        )

    else:
        return f"Unknown vault action: '{action}'. Available: get_proceedings | list | update | backup"


# ── Tool Declaration (auto-discovered by core/action_loader.py) ──────────────
TOOL = {
    "name": "project_vault",
    "description": (
        "Manages Anas Raheem's ongoing projects, proceedings memory, and safe backups: "
        "recalls what the last proceedings/progress were on any project, lists all active projects, "
        "updates milestones/next steps, and creates safe zip backups to external safe storage. "
        "Use this whenever the user asks about ongoing projects, what was done last time, or to keep safe backups."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "get_proceedings | list | update | backup"
            },
            "project_name": {
                "type": "STRING",
                "description": "Project name or identifier (e.g. Obrix Labs, Unilistics, Nokar, NeuroScout)"
            },
            "proceedings": {
                "type": "STRING",
                "description": "Summary of what was accomplished or latest proceedings"
            },
            "next_steps": {
                "type": "STRING",
                "description": "Next tasks or upcoming milestones"
            },
            "status": {
                "type": "STRING",
                "description": "active | in_progress | completed | paused"
            },
            "folder_path": {
                "type": "STRING",
                "description": "Local filesystem folder path for the project"
            },
            "destination": {
                "type": "STRING",
                "description": "Optional custom safe backup directory"
            }
        },
        "required": ["action"]
    },
    "handler": project_vault,
}
