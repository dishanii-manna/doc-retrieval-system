"""
Metadata API Routes - List books and get individual book metadata.
Reads from Elasticsearch (aggregated) or a local cache.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from search.es_client import get_es_client, ES_INDEX

router = APIRouter()


class BookInfo(BaseModel):
    doc_id: str
    title: str
    author: str
    year: Optional[int]
    publisher: str
    language: str
    paragraph_count: int


@router.get("/books", response_model=List[BookInfo])
def list_books(
    author: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
):
    """
    List all indexed books with their metadata.
    Uses an Elasticsearch aggregation (collapse by doc_id).
    """
    es = get_es_client()

    filter_clauses = []
    if author:
        filter_clauses.append({"match": {"author": author}})
    if year_from or year_to:
        range_q = {"range": {"year": {}}}
        if year_from:
            range_q["range"]["year"]["gte"] = year_from
        if year_to:
            range_q["range"]["year"]["lte"] = year_to
        filter_clauses.append(range_q)

    es_query = {
        "query": {"bool": {"filter": filter_clauses}} if filter_clauses else {"match_all": {}},
        "aggs": {
            "by_book": {
                "terms": {"field": "doc_id", "size": 1000},
                "aggs": {
                    "title":     {"terms": {"field": "book_title.keyword", "size": 1}},
                    "author":    {"terms": {"field": "author.keyword", "size": 1}},
                    "publisher": {"terms": {"field": "publisher", "size": 1}},
                    "year":      {"max":   {"field": "year"}},
                }
            }
        },
        "size": 0,
    }

    try:
        response = es.search(index=ES_INDEX, body=es_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    books = []
    for bucket in response["aggregations"]["by_book"]["buckets"]:
        doc_id = bucket["key"]

        # Skip the sample book_001
        if doc_id == "book_001":
            continue

        def first_bucket(agg_name):
            buckets = bucket.get(agg_name, {}).get("buckets", [])
            return buckets[0]["key"] if buckets else ""

        year_val = bucket["year"]["value"]
        books.append(BookInfo(
            doc_id=doc_id,
            title=first_bucket("title") or doc_id,
            author=first_bucket("author"),
            year=int(year_val) if year_val else None,
            publisher=first_bucket("publisher"),
            language="English",
            paragraph_count=bucket["doc_count"],
        ))

    books.sort(key=lambda b: b.title.lower())
    return books


@router.get("/books/{doc_id}")
def get_book(doc_id: str):
    """Get metadata and stats for a single book."""
    es = get_es_client()

    es_query = {
        "query": {"term": {"doc_id": doc_id}},
        "_source": ["doc_id", "book_title", "author", "year", "publisher"],
        "size": 1,
        "aggs": {
            "max_page": {"max": {"field": "page_number"}},
            "para_count": {"value_count": {"field": "para_id"}},
        }
    }

    try:
        response = es.search(index=ES_INDEX, body=es_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not response["hits"]["hits"]:
        raise HTTPException(status_code=404, detail=f"Book '{doc_id}' not found in index.")

    src = response["hits"]["hits"][0]["_source"]
    aggs = response["aggregations"]

    return {
        "doc_id":          src["doc_id"],
        "title":           src.get("book_title", doc_id),
        "author":          src.get("author", ""),
        "year":            src.get("year"),
        "publisher":       src.get("publisher", ""),
        "language":        "English",
        "max_page":        int(aggs["max_page"]["value"] or 0),
        "paragraph_count": int(aggs["para_count"]["value"] or 0),
    }
