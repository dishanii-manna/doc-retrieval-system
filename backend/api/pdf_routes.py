from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
import fitz
import os
import re

router = APIRouter()
PDF_DIR = os.getenv("PDF_DIR", "data/pdfs")


def get_pdf_path(doc_id: str) -> str:
    pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(PDF_DIR, doc_id)
    return pdf_path


def get_variants(keyword: str):
    kw = keyword.strip()
    return list(dict.fromkeys([
        kw,
        kw.lower(),
        kw.upper(),
        kw.capitalize(),
        ' '.join(w.capitalize() for w in kw.split()),
        kw.replace(' ', '-'),
        kw.replace(' ', '-').lower(),
        kw.replace('-', ' '),
        kw.replace('-', ' ').lower(),
    ]))


def highlight_text_layer(page, keyword: str) -> bool:
    instances = page.search_for(keyword.strip())
    if instances:
        for rect in instances:
            page.draw_rect(
                fitz.Rect(rect.x0 - 1, rect.y0 - 2, rect.x1 + 1, rect.y1 + 2),
                color=(0.9, 0.7, 0),
                fill=(1, 0.95, 0.2),
                fill_opacity=0.6,
                width=0,
            )
        return True
    return False


def normalize(text: str) -> str:
    return re.sub(r"[^\w]", "", text.lower())


def build_kw_variants(keyword: str):
    variants_set = []
    for v in get_variants(keyword):
        words = [normalize(w) for w in v.split()]
        words = [w for w in words if w]
        if words and words not in variants_set:
            variants_set.append(words)
        single = normalize(v)
        if single and [single] not in variants_set:
            variants_set.append([single])
    return variants_set


def highlight_scanned_page(page, keyword: str, zoom: float) -> bytes:
    import cv2
    import numpy as np
    import pytesseract

    mat = fitz.Matrix(4.0, 4.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    nparr = np.frombuffer(pix.tobytes("png"), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    data = pytesseract.image_to_data(
        thresh, output_type=pytesseract.Output.DICT,
        lang="eng", config="--psm 6"
    )

    kw_variants = build_kw_variants(keyword)

    ocr_words = []
    for i, word in enumerate(data["text"]):
        if not word or not word.strip():
            continue
        clean = normalize(word.strip())
        if clean:
            ocr_words.append({
                "norm": clean,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
            })

    for kw_words in kw_variants:
        n = len(kw_words)
        for i in range(len(ocr_words) - n + 1):
            match = all(
                ocr_words[i+j]["norm"].startswith(kw_words[j]) or
                ocr_words[i+j]["norm"] == kw_words[j]
                for j in range(n)
            )
            if match:
                matched = ocr_words[i:i+n]
                x1 = min(m["x"] for m in matched) - 2
                y1 = min(m["y"] for m in matched) - 2
                x2 = max(m["x"] + m["w"] for m in matched) + 2
                y2 = max(m["y"] + m["h"] for m in matched) + 2
                overlay = img.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), -1)
                img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 180, 0), 3)

    final_w = int(w * zoom / 4.0)
    final_h = int(h * zoom / 4.0)
    img = cv2.resize(img, (final_w, final_h), interpolation=cv2.INTER_AREA)

    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


@router.get("/{doc_id}/page/{page_number}")
def get_pdf_page(
        doc_id: str,
        page_number: int,
        zoom: float = Query(1.5, ge=0.5, le=4.0),
        fmt: str = Query("png"),
        highlight: Optional[str] = Query(None),
        bbox_x0: Optional[float] = Query(None),
        bbox_y0: Optional[float] = Query(None),
        bbox_x1: Optional[float] = Query(None),
        bbox_y1: Optional[float] = Query(None),
):
    pdf_path = get_pdf_path(doc_id)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found: {doc_id}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not open PDF: {e}")

    page_index = page_number - 1
    if page_index < 0 or page_index >= len(doc):
        doc.close()
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found.")

    try:
        page = doc[page_index]
        page_rect = page.rect
        page_w = page_rect.x1 - page_rect.x0
        page_h = page_rect.y1 - page_rect.y0

        raw_text = page.get_text().strip()
        has_text_layer = len(raw_text) > 100 and bool(re.search(r'[a-zA-Z]{3,}', raw_text))

        if all(v is not None for v in [bbox_x0, bbox_y0, bbox_x1, bbox_y1]):
            x0 = page_rect.x0 + bbox_x0 * page_w
            y0 = page_rect.y0 + bbox_y0 * page_h
            x1 = page_rect.x0 + bbox_x1 * page_w
            y1 = page_rect.y0 + bbox_y1 * page_h
            page.draw_rect(
                fitz.Rect(x0 - 2, y0 - 3, x1 + 2, y1 + 3),
                color=(0.9, 0.7, 0), fill=(1, 0.95, 0.2),
                fill_opacity=0.5, width=0,
            )
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")

        elif highlight and len(highlight.strip()) > 1:
            if has_text_layer:
                found = False
                for variant in get_variants(highlight):
                    if highlight_text_layer(page, variant):
                        found = True
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                if not found:
                    try:
                        img_bytes = highlight_scanned_page(page, highlight, zoom)
                    except Exception:
                        pass
            else:
                try:
                    img_bytes = highlight_scanned_page(page, highlight, zoom)
                except Exception as e:
                    print(f"[OCR highlight] Failed: {e}")
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img_bytes = pix.tobytes("png")
        else:
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")

        doc.close()
        return Response(content=img_bytes, media_type="image/png")

    except Exception as e:
        doc.close()
        raise HTTPException(status_code=500, detail=f"Render error: {e}")


@router.get("/{doc_id}/info")
def get_pdf_info(doc_id: str):
    pdf_path = get_pdf_path(doc_id)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found: {doc_id}")
    try:
        doc = fitz.open(pdf_path)
        meta = doc.metadata
        page_count = len(doc)
        doc.close()
        return {"doc_id": doc_id, "page_count": page_count, "pdf_metadata": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/download")
def download_pdf(doc_id: str):
    from fastapi.responses import FileResponse
    pdf_path = get_pdf_path(doc_id)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF not found: {doc_id}")
    return FileResponse(
        path=pdf_path, media_type="application/pdf", filename=f"{doc_id}.pdf"
    )

