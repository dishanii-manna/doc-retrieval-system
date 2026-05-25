"""
Elasticsearch Indexer - Bulk-indexes parsed paragraphs into Elasticsearch.
"""
from elasticsearch import helpers
from search.es_client import get_es_client, ES_INDEX
from ingestion.ocr_parser import Paragraph
from typing import Dict, List


def build_action(paragraph: Paragraph, book_meta: dict) -> dict:
    """Build a single Elasticsearch bulk action document."""
    source = {
        "doc_id":           paragraph.doc_id,
        "para_id":          paragraph.para_id,
        "paragraph_index":  paragraph.paragraph_index,
        "page_number":      paragraph.page_number,
        "text":             paragraph.text,
        "source_pdf":       f"{paragraph.doc_id}.pdf",
        # Book metadata
        "book_title":       book_meta.get("title", ""),
        "author":           book_meta.get("author", ""),
        "year":             book_meta.get("year"),
        "publisher":        book_meta.get("publisher", ""),
        "language":         book_meta.get("language", ""),
    }
    # Store bounding box if available
    if paragraph.bbox is not None:
        source["bbox"] = paragraph.bbox

    return {
        "_index": ES_INDEX,
        "_id":    paragraph.para_id,
        "_source": source,
    }


def index_paragraphs(
    all_paragraphs: Dict[str, List[Paragraph]],
    all_metadata: Dict[str, dict],
    chunk_size: int = 500
) -> dict:
    es = get_es_client()
    actions = []
    total = 0
    for doc_id, paragraphs in all_paragraphs.items():
        book_meta = all_metadata.get(doc_id, {"doc_id": doc_id})
        for para in paragraphs:
            actions.append(build_action(para, book_meta))
            total += 1
    if not actions:
        print("No paragraphs to index.")
        return {"indexed": 0, "errors": 0}
    print(f"Indexing {total} paragraphs in chunks of {chunk_size}...")
    success, errors = helpers.bulk(
        es,
        actions,
        chunk_size=chunk_size,
        raise_on_error=False,
        stats_only=False,
    )
    print(f"Indexed: {success} | Errors: {len(errors)}")
    if errors:
        for err in errors[:5]:
            print(f"  Error: {err}")
    return {"indexed": success, "errors": len(errors)}


def index_single_document(
    doc_id: str,
    paragraphs: List[Paragraph],
    book_meta: dict
) -> dict:
    return index_paragraphs({doc_id: paragraphs}, {doc_id: book_meta})
