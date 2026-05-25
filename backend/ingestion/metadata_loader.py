"""
Metadata Loader - Reads book metadata (CSV or JSON) and provides
a mapping from doc_id to metadata fields.

Expected columns/keys: doc_id, title, author, year, publisher, language, description
"""

import csv
import json
import os
from typing import Dict, Optional


def load_metadata(filepath: str) -> Dict[str, dict]:
    """
    Load book metadata from a CSV or JSON file.

    Args:
        filepath: Path to metadata.csv or metadata.json

    Returns:
        dict mapping doc_id -> metadata dict
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":
        return _load_csv(filepath)
    elif ext == ".json":
        return _load_json(filepath)
    else:
        raise ValueError(f"Unsupported metadata format: {ext}. Use .csv or .json")


def _load_csv(filepath: str) -> Dict[str, dict]:
    metadata = {}
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("doc_id", "").strip()
            if not doc_id:
                continue
            metadata[doc_id] = {
                "doc_id":      doc_id,
                "title":       row.get("title", "Unknown Title").strip(),
                "author":      row.get("author", "Unknown Author").strip(),
                "year":        _safe_int(row.get("year")),
                "publisher":   row.get("publisher", "").strip(),
                "language":    row.get("language", "English").strip(),
                "description": row.get("description", "").strip(),
            }
    print(f"Loaded metadata for {len(metadata)} books from CSV.")
    return metadata


def _load_json(filepath: str) -> Dict[str, dict]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Support both list and dict formats
    if isinstance(data, list):
        books = data
    elif isinstance(data, dict):
        books = list(data.values())
    else:
        raise ValueError("JSON metadata must be a list of book objects or a dict keyed by doc_id.")

    metadata = {}
    for book in books:
        doc_id = book.get("doc_id", "").strip()
        if not doc_id:
            continue
        metadata[doc_id] = {
            "doc_id":      doc_id,
            "title":       book.get("title", "Unknown Title"),
            "author":      book.get("author", "Unknown Author"),
            "year":        _safe_int(book.get("year")),
            "publisher":   book.get("publisher", ""),
            "language":    book.get("language", "English"),
            "description": book.get("description", ""),
        }
    print(f"Loaded metadata for {len(metadata)} books from JSON.")
    return metadata


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_book_meta(metadata: Dict[str, dict], doc_id: str) -> dict:
    """Return metadata for a doc_id, with safe defaults."""
    return metadata.get(doc_id, {
        "doc_id":      doc_id,
        "title":       "Unknown Title",
        "author":      "Unknown Author",
        "year":        None,
        "publisher":   "",
        "language":    "",
        "description": "",
    })


# ── Example metadata.csv format ────────────────────────────────────────────────
#
# doc_id,title,author,year,publisher,language,description
# book_001,The Adventures of Tom Sawyer,Mark Twain,1876,American Publishing Company,English,A novel about a boy growing up along the Mississippi River.
# book_002,Pride and Prejudice,Jane Austen,1813,T. Egerton,English,A romantic novel of manners.
