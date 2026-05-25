"""
Elasticsearch client configuration and index management.
"""

from elasticsearch import Elasticsearch
import os

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "book_paragraphs")

es = Elasticsearch([ES_HOST])

PARAGRAPH_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id":       {"type": "keyword"},
            "para_id":      {"type": "keyword"},
            "page_number":  {"type": "integer"},
            "paragraph_index": {"type": "integer"},
            "text":         {"type": "text", "analyzer": "english"},
            "book_title":   {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "author":       {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "year":         {"type": "integer"},
            "publisher":    {"type": "keyword"},
            "source_pdf":   {"type": "keyword"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "english": {
                    "type": "english"
                }
            }
        }
    }
}


def create_index(delete_if_exists: bool = False):
    """Create the Elasticsearch index with proper mappings."""
    if es.indices.exists(index=ES_INDEX):
        if delete_if_exists:
            es.indices.delete(index=ES_INDEX)
            print(f"Deleted existing index: {ES_INDEX}")
        else:
            print(f"Index '{ES_INDEX}' already exists. Skipping creation.")
            return

    es.indices.create(index=ES_INDEX, body=PARAGRAPH_MAPPING)
    print(f"Created index: {ES_INDEX}")


def get_es_client():
    return es


def check_connection():
    try:
        info = es.info()
        return True, info["version"]["number"]
    except Exception as e:
        return False, str(e)
