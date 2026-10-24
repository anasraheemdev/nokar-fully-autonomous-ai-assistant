"""
memory/rag_engine.py — High-Performance Retrieval-Augmented Generation (RAG) System.

Features:
  • Long-context knowledge indexing across user profile, active goals, companies,
    socials, technical skills, and ongoing project states.
  • Local TF-IDF & vector cosine scoring (using NumPy) — zero latency, fully offline,
    no external vector DB setup required.
  • Auto-ingests memory/profile.json, memory/long_term.json, and ongoing project states.
  • Dynamic chunking and relevance ranking to inject into Nokar's prompts.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = BASE_DIR / "memory" / "profile.json"
LONG_TERM_PATH = BASE_DIR / "memory" / "long_term.json"
PROJECTS_VAULT_PATH = BASE_DIR / "memory" / "ongoing_projects.json"


class RAGDocument:
    def __init__(self, doc_id: str, content: str, category: str = "general", metadata: dict = None):
        self.doc_id = doc_id
        self.content = content.strip()
        self.category = category
        self.metadata = metadata or {}
        self.tokens = self._tokenize(self.content)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]


class RAGEngine:
    def __init__(self):
        self.documents: list[RAGDocument] = []
        self._doc_freqs: Counter = Counter()
        self._total_docs: int = 0
        self._is_indexed: bool = False
        self.reload()

    def reload(self) -> None:
        """Reload and re-index all knowledge bases."""
        self.documents = []
        self._load_profile()
        self._load_long_term_memory()
        self._load_ongoing_projects()
        self._build_index()

    def _load_profile(self) -> None:
        if not PROFILE_PATH.exists():
            return
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            
            # Identity & General
            ident = data.get("identity", {})
            self.documents.append(RAGDocument(
                doc_id="profile_identity",
                category="identity",
                content=(
                    f"User Identity: {ident.get('full_name')} ({ident.get('preferred_short_name')}), "
                    f"Salutation: {ident.get('salutation', 'Sir Anas')}. "
                    f"Born in {ident.get('birthplace')} ({ident.get('hometown')}), "
                    f"resides in {ident.get('residence_region')}. "
                    f"Roles: {', '.join(ident.get('roles', []))}. "
                    f"Languages: {', '.join(ident.get('languages', []))}."
                ),
                metadata=ident
            ))

            # Contacts & Socials
            contacts = data.get("contacts", {})
            socials = data.get("online_presence", {})
            self.documents.append(RAGDocument(
                doc_id="profile_contacts_socials",
                category="contacts",
                content=(
                    f"Contacts & Socials of Anas Raheem: "
                    f"Personal Email: {contacts.get('primary_personal_email')}, "
                    f"Work Email: {contacts.get('work_email')}, "
                    f"Phone/WhatsApp: {contacts.get('phone')} ({contacts.get('whatsapp')}). "
                    f"LinkedIn: {socials.get('linkedin')}, "
                    f"GitHub: {socials.get('github')} ({socials.get('github_username')}), "
                    f"Personal Site: {socials.get('personal_site')}, "
                    f"Company Site: {socials.get('company_website')}, "
                    f"Unilistics: {socials.get('unilistics_website')}."
                ),
                metadata={**contacts, **socials}
            ))

            # Companies: Obrix Labs & Unilistics
            companies = data.get("companies", {})
            obrix = companies.get("obrix_labs", {})
            self.documents.append(RAGDocument(
                doc_id="company_obrix_labs",
                category="company",
                content=(
                    f"Company Obrix Labs: Anas Raheem is Founder & CEO. "
                    f"Website: {obrix.get('website')}, Contact: {obrix.get('contact')}. "
                    f"Services provided: {', '.join(obrix.get('services', []))}."
                ),
                metadata=obrix
            ))

            unilistics = companies.get("unilistics", {})
            self.documents.append(RAGDocument(
                doc_id="company_unilistics",
                category="company",
                content=(
                    f"Company Unilistics: Founded by Anas Raheem (formerly Mentora). "
                    f"Description: {unilistics.get('description')}. "
                    f"Features: {', '.join(unilistics.get('features', []))}. "
                    f"Tech Stack: {', '.join(unilistics.get('technology', []))}."
                ),
                metadata=unilistics
            ))

            # Education
            edu = data.get("education", {})
            self.documents.append(RAGDocument(
                doc_id="profile_education",
                category="education",
                content=(
                    f"Education of Anas Raheem: "
                    f"School: {edu.get('school')}. "
                    f"Air University: {edu.get('air_university')}. "
                    f"Virtual University: {edu.get('virtual_university')}. "
                    f"IELTS: {json.dumps(edu.get('ielts', {}))}. "
                    f"Studied: {', '.join(edu.get('areas_studied', []))}."
                ),
                metadata=edu
            ))

            # Skills
            skills = data.get("technical_skills", {})
            self.documents.append(RAGDocument(
                doc_id="profile_skills",
                category="skills",
                content=(
                    f"Technical Skills of Anas Raheem: "
                    f"Languages: {', '.join(skills.get('languages', []))}. "
                    f"Frontend: {', '.join(skills.get('frontend', []))}. "
                    f"Backend: {', '.join(skills.get('backend', []))}. "
                    f"Databases: {', '.join(skills.get('databases', []))}. "
                    f"AI & ML: {', '.join(skills.get('ml_and_ai', []))}. "
                    f"Other: {', '.join(skills.get('other', []))}."
                ),
                metadata=skills
            ))

            # Goals
            goals = data.get("goals", [])
            self.documents.append(RAGDocument(
                doc_id="profile_goals",
                category="goals",
                content=f"Anas Raheem's Primary Goals: {'; '.join(goals)}.",
                metadata={"goals": goals}
            ))

            # Selected Projects
            projects = data.get("selected_projects", [])
            self.documents.append(RAGDocument(
                doc_id="profile_selected_projects",
                category="projects",
                content=f"Key Research & Engineering Projects of Anas Raheem: {'; '.join(projects)}.",
                metadata={"projects": projects}
            ))

            # Research Interests
            research = data.get("research_interests", [])
            self.documents.append(RAGDocument(
                doc_id="profile_research",
                category="research",
                content=f"Research Interests of Anas Raheem: {'; '.join(research)}.",
                metadata={"research": research}
            ))

        except Exception as e:
            print(f"[RAG] Error loading profile: {e}")

    def _load_long_term_memory(self) -> None:
        if not LONG_TERM_PATH.exists():
            return
        try:
            data = json.loads(LONG_TERM_PATH.read_text(encoding="utf-8"))
            for category, items in data.items():
                if isinstance(items, dict):
                    chunk_parts = []
                    for k, v in items.items():
                        val = v.get("value", "") if isinstance(v, dict) else str(v)
                        chunk_parts.append(f"{k}: {val}")
                    if chunk_parts:
                        self.documents.append(RAGDocument(
                            doc_id=f"memory_{category}",
                            category=category,
                            content=f"Stored {category} memory: {'; '.join(chunk_parts)}.",
                            metadata=items
                        ))
        except Exception as e:
            print(f"[RAG] Error loading long term memory: {e}")

    def _load_ongoing_projects(self) -> None:
        if not PROJECTS_VAULT_PATH.exists():
            return
        try:
            data = json.loads(PROJECTS_VAULT_PATH.read_text(encoding="utf-8"))
            for proj_name, info in data.items():
                if isinstance(info, dict):
                    self.documents.append(RAGDocument(
                        doc_id=f"project_{proj_name}",
                        category="ongoing_project",
                        content=(
                            f"Ongoing Project '{proj_name}': Status={info.get('status', 'active')}. "
                            f"Path={info.get('path', 'N/A')}. "
                            f"Last Proceedings={info.get('last_proceedings', 'None')}. "
                            f"Next Milestones={info.get('next_steps', 'None')}. "
                            f"Safe Backup Location={info.get('backup_location', 'None')}."
                        ),
                        metadata=info
                    ))
        except Exception as e:
            print(f"[RAG] Error loading ongoing projects: {e}")

    def _build_index(self) -> None:
        self._doc_freqs.clear()
        self._total_docs = len(self.documents)
        for doc in self.documents:
            unique_tokens = set(doc.tokens)
            for token in unique_tokens:
                self._doc_freqs[token] += 1
        self._is_indexed = True

    def query(self, query_text: str, top_k: int = 3, min_score: float = 0.05) -> list[tuple[RAGDocument, float]]:
        """Retrieve top_k most relevant knowledge chunks matching query_text."""
        if not self._is_indexed:
            self._build_index()

        q_tokens = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 1]
        if not q_tokens or self._total_docs == 0:
            return []

        q_counter = Counter(q_tokens)
        scores = []

        for doc in self.documents:
            doc_counter = Counter(doc.tokens)
            doc_len = len(doc.tokens) or 1
            score = 0.0

            for token, q_tf in q_counter.items():
                if token in doc_counter:
                    # Term frequency in document
                    tf = doc_counter[token] / doc_len
                    # Inverse document frequency
                    df = self._doc_freqs.get(token, 1)
                    idf = math.log((self._total_docs + 1) / (df + 0.5)) + 1.0
                    score += tf * idf * q_tf

                    # Category boost
                    if token in doc.category.lower():
                        score += 0.5

            if score >= min_score:
                scores.append((doc, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def format_context_for_query(self, query_text: str, top_k: int = 3) -> str:
        """Return formatted markdown snippet of retrieved context for Gemini."""
        hits = self.query(query_text, top_k=top_k)
        if not hits:
            return ""
        lines = ["[RELEVANT KNOWLEDGE CONTEXT]"]
        for doc, score in hits:
            lines.append(f"• {doc.content}")
        return "\n".join(lines)

    def get_system_context(self) -> str:
        """
        Produce a concise executive briefing of Anas Raheem's identity, key goals,
        and current ongoing projects for system prompt injection.
        """
        lines = [
            "[USER PROFILE, GOALS & ONGOING INITIATIVES]",
            "• User: Muhammad Anas Raheem (address as 'Sir Anas' or 'Anas Raheem').",
            "• Key Roles: Founder & CEO of Obrix Labs | Founder of Unilistics | AI Engineer & Full-Stack Developer.",
            "• Primary Goals: Scale Obrix Labs; Scale Unilistics global admissions platform; International AI research; Trustworthy clinical AI/oncology decision support; Autonomous AI agents.",
            "• Assistant Persona: Your name is 'Nokar' — Anas Raheem's loyal, respectful, and highly competent AI operator.",
        ]

        # Add ongoing projects summary
        if PROJECTS_VAULT_PATH.exists():
            try:
                pdata = json.loads(PROJECTS_VAULT_PATH.read_text(encoding="utf-8"))
                if pdata:
                    lines.append("• Active Ongoing Projects in Vault:")
                    for pid, p in pdata.items():
                        pname = p.get("name", pid)
                        proc = p.get("last_proceedings", "In progress")
                        status = p.get("status", "active")
                        lines.append(f"  - {pname} [{status}]: {proc}")
            except Exception:
                pass

        return "\n".join(lines)


# Singleton instance
_rag_instance: Optional[RAGEngine] = None


def get_rag() -> RAGEngine:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance


def get_rag_engine() -> RAGEngine:
    return get_rag()


def query_rag_context(query: str, top_k: int = 3) -> str:
    """Convenience function for LLM injection."""
    return get_rag().format_context_for_query(query, top_k=top_k)
