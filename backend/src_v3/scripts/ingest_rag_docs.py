"""Simple RAG ingestion script for ChromaDB.

Loads Markdown/text files from a directory and indexes them into
ChromaRAGService with basic metadata so the Socratic tutor can
retrieve richer context.

Usage (from repo root):

    python -m backend.src_v3.scripts.ingest_rag_docs --path docs --language python

This script is intentionally minimal and is not used by tests; it is
meant as a maintenance/ops tool.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict

# Ensure project root on sys.path (similar to load_test_data.py)
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.src_v3.infrastructure.ai.rag import ChromaRAGService  # type: ignore  # noqa: E402


def collect_documents(base_path: Path, exts: List[str]) -> tuple[List[str], List[Dict], List[str]]:
    """Collect documents recursively from base_path.

    Returns (documents, metadatas, ids).
    """
    documents: List[str] = []
    metadatas: List[Dict] = []
    ids: List[str] = []

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            # Skip unreadable files silently; this is a best-effort tool
            continue

        rel_path = str(path.relative_to(base_path))
        doc_id = f"{rel_path}"

        documents.append(text)
        metadatas.append(
            {
                "path": rel_path,
                "filename": path.name,
                "source": "filesystem",
            }
        )
        ids.append(doc_id)

    return documents, metadatas, ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local docs into Chroma RAG store")
    parser.add_argument("--path", type=str, default="docs", help="Base directory with docs to ingest")
    parser.add_argument(
        "--language",
        type=str,
        default="python",
        help="Logical language tag to store in metadata (for filtering)",
    )
    parser.add_argument(
        "--exts",
        type=str,
        default=".md,.txt,.py",
        help="Comma-separated list of file extensions to ingest",
    )

    args = parser.parse_args()

    base_path = Path(args.path).resolve()
    if not base_path.exists() or not base_path.is_dir():
        print(f"❌ Path not found or not a directory: {base_path}")
        raise SystemExit(1)

    exts = [e.strip().lower() for e in args.exts.split(",") if e.strip()]
    print(f"📂 Ingesting documents from: {base_path}")
    print(f"   Extensions: {exts}")

    documents, metadatas, ids = collect_documents(base_path, exts)
    if not documents:
        print("⚠️  No documents found to ingest.")
        return

    # Attach language metadata
    for meta in metadatas:
        meta["language"] = args.language

    rag_service = ChromaRAGService()
    print(f"🧠 Adding {len(documents)} documents to collection '{rag_service.collection_name}'...")

    rag_service.add_documents(documents=documents, metadatas=metadatas, ids=ids)

    print("✅ RAG ingestion completed.")


if __name__ == "__main__":  # pragma: no cover - manual script
    main()
