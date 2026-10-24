"""
core/rag_vault.py — Local Document RAG (Retrieval-Augmented Generation) Vault.

Features:
  • Autonomous indexing of user-provided code, documents, and uploaded files.
  • Text extraction from .txt, .md, .py, .json, .csv, .log, .pdf, .html, .js, .ts.
  • Robust chunking with contextual overlap and line numbers.
  • Fast local TF-IDF & Cosine Similarity vector engine with zero heavy pip dependencies.
  • Persistent index storage in memory/rag_vault.json.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT_STORAGE_PATH = BASE_DIR / "memory" / "rag_vault.json"
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".py", ".json", ".csv", ".log",
    ".html", ".htm", ".js", ".ts", ".jsx", ".tsx", ".css", ".java",
    ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".yaml", ".yml",
    ".sh", ".bat", ".ps1", ".pdf"
}


def _tokenize(text: str) -> list[str]:
    """Extract lowercased alphanumeric word tokens."""
    return [w for w in re.findall(r"[a-z0-9_]{2,}", text.lower())]


def _extract_text(file_path: Path) -> str:
    """Extract plain text from supported document types."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            pages_text = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages_text)
        except Exception:
            try:
                import pypdf2
                reader = pypdf2.PdfReader(str(file_path))
                return "\n".join([p.extract_text() or "" for p in reader.pages])
            except Exception:
                pass

    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[Error reading file: {e}]"


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks without breaking mid-sentence where possible."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            brk = text.rfind("\n", start + overlap, end)
            if brk == -1:
                brk = text.rfind(". ", start + overlap, end)
            if brk != -1:
                end = brk + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end < len(text) else len(text)
    return chunks


class RagVault:
    """Manages the local document vector database."""

    def __init__(self, storage_path: Path = VAULT_STORAGE_PATH):
        self.storage_path = storage_path
        self.documents: dict[str, dict[str, Any]] = {}
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.documents = data.get("documents", {})
            self._recalculate_idf()
        except Exception as e:
            print(f"[RAG Vault] ⚠️ Failed to load index: {e}")

    def _save(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "documents": self.documents,
            }
            self.storage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[RAG Vault] ⚠️ Failed to save index: {e}")

    def _recalculate_idf(self) -> None:
        all_chunks: list[list[str]] = []
        for doc in self.documents.values():
            for ch in doc.get("chunks", []):
                tokens = set(_tokenize(ch.get("text", "")))
                if tokens:
                    all_chunks.append(list(tokens))

        n_docs = len(all_chunks)
        if not n_docs:
            self.idf.clear()
            return

        df: dict[str, int] = {}
        for token_set in all_chunks:
            for t in token_set:
                df[t] = df.get(t, 0) + 1

        self.idf = {t: math.log((1 + n_docs) / (1 + count)) + 1.0 for t, count in df.items()}

    def _tfidf_vector(self, text: str) -> dict[str, float]:
        tokens = _tokenize(text)
        if not tokens:
            return {}
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        total = float(len(tokens))
        vec: dict[str, float] = {}
        norm_sq = 0.0
        for t, count in tf.items():
            w = (count / total) * self.idf.get(t, 1.0)
            vec[t] = w
            norm_sq += w * w
        norm = math.sqrt(norm_sq) or 1.0
        return {t: val / norm for t, val in vec.items()}

    def _cosine_sim(self, v1: dict[str, float], v2: dict[str, float]) -> float:
        if not v1 or not v2:
            return 0.0
        s, l = (v1, v2) if len(v1) < len(v2) else (v2, v1)
        return sum(val * l[k] for k, val in s.items() if k in l)

    def index_file(self, file_path: Path | str) -> int:
        """Index or update a single file. Returns chunk count."""
        p = Path(file_path).resolve()
        if not p.exists() or not p.is_file():
            return 0
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS and p.name.upper() not in ("LICENSE", "NOTICE", "DOCKERFILE", "MAKEFILE"):
            return 0

        mtime = p.stat().st_mtime
        key = str(p)

        existing = self.documents.get(key)
        if existing and existing.get("mtime") == mtime:
            return len(existing.get("chunks", []))

        text = _extract_text(p)
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        chunk_data = []
        for i, c in enumerate(chunks):
            chunk_data.append({
                "id": i,
                "text": c,
            })

        self.documents[key] = {
            "name": p.name,
            "path": str(p),
            "mtime": mtime,
            "chunks": chunk_data,
        }

        self._recalculate_idf()
        self._save()
        return len(chunks)

    def index_directory(self, dir_path: Path | str, max_files: int = 50) -> dict[str, int]:
        """Index a folder recursively up to max_files."""
        p = Path(dir_path).resolve()
        if not p.exists() or not p.is_dir():
            return {}

        results: dict[str, int] = {}
        count = 0
        for root, _, files in os.walk(p):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    fp = Path(root) / f
                    c = self.index_file(fp)
                    if c > 0:
                        results[fp.name] = c
                        count += 1
                        if count >= max_files:
                            break
            if count >= max_files:
                break
        return results

    def query(self, query_text: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Search the vault for relevant snippets matching query."""
        if not self.documents:
            return []

        q_vec = self._tfidf_vector(query_text)
        if not q_vec:
            return []

        scores: list[tuple[float, str, str, str]] = []

        for doc in self.documents.values():
            fn = doc.get("name", "Document")
            fp = doc.get("path", "")
            for ch in doc.get("chunks", []):
                txt = ch.get("text", "")
                c_vec = self._tfidf_vector(txt)
                sim = self._cosine_sim(q_vec, c_vec)
                if sim > 0.05:
                    scores.append((sim, fn, fp, txt))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, fn, fp, txt in scores[:top_k]:
            results.append({
                "score": round(score, 3),
                "file_name": fn,
                "file_path": fp,
                "snippet": txt,
            })
        return results

    def get_stats(self) -> dict[str, Any]:
        total_chunks = sum(len(d.get("chunks", [])) for d in self.documents.values())
        return {
            "total_files": len(self.documents),
            "total_chunks": total_chunks,
            "files": [d.get("name") for d in self.documents.values()],
        }


_vault = RagVault()


def get_vault() -> RagVault:
    global _vault
    return _vault
