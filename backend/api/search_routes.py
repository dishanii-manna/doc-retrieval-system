"""
Search API Routes - Full-text search over indexed paragraphs.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from search.es_client import get_es_client, ES_INDEX

router = APIRouter()


class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class ParagraphResult(BaseModel):
    para_id: str
    doc_id: str
    page_number: int
    paragraph_index: int
    text: str
    highlight: Optional[str] = None
    score: float
    book_title: str
    author: str
    year: Optional[int]
    publisher: str
    source_pdf: str
    bbox: Optional[BBox] = None

class SearchResponse(BaseModel):
    total: int
    query: str
    results: List[ParagraphResult]


@router.get("/", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Search query text"),
    size: int = Query(10, ge=1, le=50, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    doc_id: Optional[str] = Query(None, description="Filter by document ID"),
    author: Optional[str] = Query(None, description="Filter by author"),
    year_from: Optional[int] = Query(None, description="Filter by year (from)"),
    year_to: Optional[int] = Query(None, description="Filter by year (to)"),
):
    """
    Full-text search over indexed OCR paragraphs.
    Supports filters by doc_id, author, and year range.
    Fuzziness disabled — stemming handles word variants (love/loved/loving).
    Fuzzy matching was causing unrelated words like 'rove' and 'move' to match 'love'.
    """
    es = get_es_client()

    # Build query
    # NOTE: fuzziness set to 0 (disabled) to prevent misleading matches for humanities users.
    # The English analyser's stemming already handles variants: love→loved→loving etc.
    must_clauses = [
        {
            "multi_match": {
                "query": q,
                "fields": ["text^3", "book_title^2", "author"],
                "type": "phrase",
            }
        }
    ]

    filter_clauses = []
    if doc_id:
        filter_clauses.append({"term": {"doc_id": doc_id}})
    if author:
        filter_clauses.append({"match": {"author": author}})
    if year_from or year_to:
        range_filter = {"range": {"year": {}}}
        if year_from:
            range_filter["range"]["year"]["gte"] = year_from
        if year_to:
            range_filter["range"]["year"]["lte"] = year_to
        filter_clauses.append(range_filter)

    es_query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        },
        "highlight": {
            "fields": {
                "text": {
                    "fragment_size": 0,
                    "number_of_fragments": 0,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"],
                }
            }
        },
        "from": offset,
        "size": size,
    }

    try:
        response = es.search(index=ES_INDEX, body=es_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch error: {str(e)}")

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    results = []
    for hit in hits:
        src = hit["_source"]
        highlight_text = None
        if "highlight" in hit and "text" in hit["highlight"]:
            highlight_text = " ... ".join(hit["highlight"]["text"])

        bbox = None
        if "bbox" in src:
            bbox = BBox(**src["bbox"])

        results.append(ParagraphResult(
            para_id=src["para_id"],
            doc_id=src["doc_id"],
            page_number=src["page_number"],
            paragraph_index=src["paragraph_index"],
            text=src["text"],
            highlight=highlight_text,
            score=hit["_score"],
            book_title=src.get("book_title", ""),
            author=src.get("author", ""),
            year=src.get("year"),
            publisher=src.get("publisher", ""),
            source_pdf=src.get("source_pdf", ""),
            bbox=bbox,
        ))

    return SearchResponse(total=total, query=q, results=results)


@router.get("/suggest")
def suggest(q: str = Query(..., description="Partial query for autocomplete")):
    """Simple prefix-based suggestion on book titles and authors."""
    es = get_es_client()

    es_query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["book_title", "author"],
                "type": "phrase_prefix",
            }
        },
        "_source": ["book_title", "author", "doc_id"],
        "size": 5,
        "collapse": {"field": "doc_id"},
    }

    try:
        response = es.search(index=ES_INDEX, body=es_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    suggestions = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        suggestions.append({
            "doc_id": src["doc_id"],
            "book_title": src.get("book_title", ""),
            "author": src.get("author", ""),
        })

    return {"suggestions": suggestions}
