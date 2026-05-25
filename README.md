# Document Processing & Retrieval System

A full-stack application for full-text search over OCR-processed historical books, with side-by-side PDF page viewing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React Frontend  (port 3000)                            │
│  SearchBar → ResultCards → Split PDF Viewer             │
└────────────────────┬────────────────────────────────────┘
                     │ /api/*
┌────────────────────▼────────────────────────────────────┐
│  FastAPI Backend  (port 8000)                           │
│  /api/search   → Elasticsearch queries                  │
│  /api/pdf      → PyMuPDF page rendering                 │
│  /api/metadata → Book info aggregations                 │
└──────┬───────────────────────────┬──────────────────────┘
       │                           │
┌──────▼──────┐           ┌────────▼─────────┐
│Elasticsearch│           │  PDF files on    │
│   (port     │           │  disk (data/pdfs)│
│   9200)     │           └──────────────────┘
└─────────────┘
```

---

## Project Structure

```
doc_retrieval_system/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── api/
│   │   ├── search_routes.py       # GET /api/search/
│   │   ├── pdf_routes.py          # GET /api/pdf/{doc_id}/page/{n}
│   │   └── metadata_routes.py     # GET /api/metadata/books
│   ├── ingestion/
│   │   ├── pipeline.py            # Run this to ingest data
│   │   ├── ocr_parser.py          # OCR → paragraph segmentation
│   │   ├── metadata_loader.py     # CSV/JSON metadata reader
│   │   └── indexer.py             # Bulk Elasticsearch indexer
│   └── search/
│       └── es_client.py           # ES connection + index mapping
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── SearchPage.jsx     # Main search + split PDF view
│   │   │   ├── BooksPage.jsx      # Library grid
│   │   │   └── BookDetailPage.jsx
│   │   ├── components/
│   │   │   ├── SearchBar.jsx      # Autocomplete search bar
│   │   │   ├── ResultCard.jsx     # Search result card
│   │   │   ├── PdfViewer.jsx      # PDF page renderer
│   │   │   └── Navbar.jsx
│   │   └── services/
│   │       └── api.js             # Axios API client
│   ├── Dockerfile
│   └── nginx.conf
├── docker/
│   └── docker-compose.yml
└── data/
    ├── pdfs/          ← Put your PDF files here (named: {doc_id}.pdf)
    ├── ocr/           ← Put your OCR .txt files here (named: {doc_id}.txt)
    └── metadata/
        └── books.csv  ← Book metadata (see format below)
```

---

## Setup & Running

### Prerequisites
- Docker & Docker Compose
- OR: Python 3.11+, Node.js 20+, Elasticsearch 8.x

### Option A: Docker (Recommended)

```bash
# 1. Add your data
cp your_books/*.pdf       data/pdfs/
cp your_books/ocr/*.txt   data/ocr/
# Edit data/metadata/books.csv with your book info

# 2. Start all services
cd docker
docker-compose up -d

# 3. Wait for Elasticsearch to be ready (~30s), then run ingestion
docker exec backend_books python -m ingestion.pipeline \
    --ocr-dir /data/ocr \
    --metadata /data/metadata/books.csv \
    --reset

# 4. Open http://localhost:3000
```

### Option B: Local Development

```bash
# Terminal 1: Elasticsearch
docker run -d -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.0

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
cp .env.example .env         # Edit as needed
python -m ingestion.pipeline --ocr-dir ../data/ocr --metadata ../data/metadata/books.csv --reset
uvicorn main:app --reload

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Data Format

### File Naming Convention
- PDF:  `data/pdfs/{doc_id}.pdf`
- OCR:  `data/ocr/{doc_id}.txt`
- The `doc_id` must match between PDF and OCR files, and in the metadata CSV.

Example:
```
data/pdfs/book_001.pdf
data/ocr/book_001.txt      ← same stem
```
And in `books.csv`: `doc_id` column = `book_001`

### OCR Text Format
The parser recognizes these page number patterns:
```
--- Page 12 ---
[Page 12]
== 12 ==
12             ← bare number on its own line
```
Paragraphs are separated by blank lines. Everything between blank lines (or page markers) is treated as one paragraph.

### Metadata CSV Format
```csv
doc_id,title,author,year,publisher,language,description
book_001,The Adventures of Tom Sawyer,Mark Twain,1876,American Publishing Company,English,A novel about...
```
JSON format is also supported (list of objects with the same keys).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search/?q=...` | Full-text search with optional filters |
| GET | `/api/search/suggest?q=...` | Autocomplete suggestions |
| GET | `/api/pdf/{doc_id}/page/{n}` | Render PDF page as image |
| GET | `/api/pdf/{doc_id}/info` | PDF page count and metadata |
| GET | `/api/pdf/{doc_id}/download` | Download original PDF |
| GET | `/api/metadata/books` | List all books |
| GET | `/api/metadata/books/{doc_id}` | Get single book info |

### Search Query Parameters
- `q` (required): search text
- `size`: results per page (default 10, max 50)
- `offset`: pagination offset
- `doc_id`: filter to one document
- `author`: filter by author name
- `year_from`, `year_to`: filter by publication year range

---

## Re-indexing

To re-ingest after adding new books:
```bash
python -m ingestion.pipeline --ocr-dir data/ocr --metadata data/metadata/books.csv
# Add --reset to wipe and rebuild the index from scratch
```
