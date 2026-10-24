"""
actions/rag_vault_action.py — Semantic Local Document & Codebase Search Tool.

Auto-discovered by core.action_loader at startup.
Allows NOKAR to query indexed personal documents, notes, uploaded files, and code.
"""

from __future__ import annotations

import json
from pathlib import Path
from core.rag_vault import get_vault


def query_rag_vault(parameters: dict = None, response=None, player=None, session_memory=None) -> str:
    params = parameters or {}
    query = (params.get("query") or params.get("search") or "").strip()
    action = (params.get("action") or "search").strip().lower()
    path = (params.get("path") or "").strip()

    vault = get_vault()

    if action in ("index", "add"):
        if not path:
            return "Please specify a file or directory path to index."
        p = Path(path).resolve()
        if p.is_file():
            c = vault.index_file(p)
            return f"Successfully indexed '{p.name}' into RAG Vault ({c} chunks)."
        elif p.is_dir():
            res = vault.index_directory(p)
            return f"Successfully indexed {len(res)} file(s) into RAG Vault ({sum(res.values())} total chunks)."
        return f"Path does not exist: {path}"

    if action == "stats":
        stats = vault.get_stats()
        return (
            f"RAG Vault Status:\n"
            f"• Indexed Files: {stats['total_files']}\n"
            f"• Total Semantic Chunks: {stats['total_chunks']}\n"
            f"• Files: {', '.join(stats['files'][:10])}{' ...' if len(stats['files']) > 10 else ''}"
        )

    if not query:
        return "What would you like me to search for in your documents or codebase?"

    results = vault.query(query, top_k=4)
    if not results:
        stats = vault.get_stats()
        if stats["total_files"] == 0:
            return (
                f"No documents are currently indexed in your RAG Vault. "
                f"You can drop files into the File Upload card or ask me to index a folder."
            )
        return f"No relevant content found in your indexed documents matching '{query}'."

    out = [f"Found {len(results)} relevant section(s) in your documents:"]
    for i, r in enumerate(results, 1):
        out.append(f"\n[{i}] Source: {r['file_name']} (Relevance: {int(r['score'] * 100)}%):")
        out.append(f"\"{r['snippet']}\"")

    return "\n".join(out)


TOOL = {
    "name": "query_rag_vault",
    "description": (
        "Search through the user's indexed local documents, uploaded files, notes, and code. "
        "Use this whenever the user asks about content from their uploaded documents, notes, "
        "or wants to retrieve specific knowledge from their files: 'what does my document say about X?', "
        "'search my notes for Y', 'find the function Z in my codebase', or to index a directory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search question or concept to retrieve from the local document vault."
            },
            "action": {
                "type": "string",
                "enum": ["search", "index", "stats"],
                "description": "'search' to query (default), 'index' to index a file/directory path, 'stats' for index status."
            },
            "path": {
                "type": "string",
                "description": "Optional file or folder path when action is 'index'."
            }
        },
        "required": ["query"]
    },
    "handler": query_rag_vault,
}
