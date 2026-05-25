"""
Ingestion Pipeline - Run this script to:
  1. Parse all OCR text files
  2. Load book metadata
  3. Index everything into Elasticsearch

Usage:
    python -m ingestion.pipeline \
        --ocr-dir data/ocr \
        --metadata data/metadata/books.csv \
        --reset

Args:
    --ocr-dir    : Directory containing OCR .txt files
    --metadata   : Path to metadata CSV or JSON file
    --reset      : If set, delete and recreate the ES index
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from search.es_client import create_index, check_connection
from ingestion.ocr_parser import parse_all_ocr_files
from ingestion.metadata_loader import load_metadata
from ingestion.indexer import index_paragraphs


def main():
    parser = argparse.ArgumentParser(description="Ingest OCR books into Elasticsearch")
    parser.add_argument("--ocr-dir",  default="data/ocr",                help="Directory with OCR .txt files")
    parser.add_argument("--metadata", default="data/metadata/books.csv", help="Path to metadata CSV or JSON")
    parser.add_argument("--reset",    action="store_true",                help="Delete and recreate ES index")
    parser.add_argument("--bbox",     action="store_true",                help="Extract bounding boxes using Tesseract (slow)")
    parser.add_argument("--pdf-dir",  default="data/pdfs",                help="Directory with PDF files (for bbox extraction)")
    args = parser.parse_args()

    # 1. Check Elasticsearch connection
    print("🔌 Checking Elasticsearch connection...")
    ok, info = check_connection()
    if not ok:
        print(f"❌ Cannot connect to Elasticsearch: {info}")
        print("   Make sure ES is running: docker-compose up -d elasticsearch")
        sys.exit(1)
    print(f"✅ Connected to Elasticsearch {info}")

    # 2. Create / reset index
    print(f"\n📐 Setting up index (reset={args.reset})...")
    create_index(delete_if_exists=args.reset)

    # 3. Load metadata
    print(f"\n📋 Loading metadata from: {args.metadata}")
    if not os.path.exists(args.metadata):
        print(f"⚠️  Metadata file not found: {args.metadata}")
        print("   Continuing without metadata (titles/authors will be blank).")
        all_metadata = {}
    else:
        all_metadata = load_metadata(args.metadata)

    # 4. Parse OCR files
    print(f"\n📖 Parsing OCR files from: {args.ocr_dir}")
    if not os.path.isdir(args.ocr_dir):
        print(f"❌ OCR directory not found: {args.ocr_dir}")
        sys.exit(1)

    all_paragraphs = parse_all_ocr_files(args.ocr_dir)
    total_paragraphs = sum(len(v) for v in all_paragraphs.values())
    print(f"   → {len(all_paragraphs)} documents, {total_paragraphs} paragraphs total")

    # 4b. Extract bounding boxes using Tesseract
    if args.bbox:
        from ingestion.ocr_parser import extract_bbox_for_paragraphs
        print(f"\n📐 Extracting bounding boxes from PDFs in: {args.pdf_dir}")
        for doc_id, paragraphs in all_paragraphs.items():
            pdf_path = os.path.join(args.pdf_dir, f"{doc_id}.pdf")
            if os.path.exists(pdf_path):
                print(f"  Processing {doc_id}...")
                extract_bbox_for_paragraphs(pdf_path, paragraphs, doc_id)
            else:
                print(f"  [skip] PDF not found: {pdf_path}")

    # 5. Index into Elasticsearch
    print(f"\n🚀 Indexing into Elasticsearch...")
    result = index_paragraphs(all_paragraphs, all_metadata)

    print(f"\n🎉 Done! {result['indexed']} paragraphs indexed, {result['errors']} errors.")


if __name__ == "__main__":
    main()