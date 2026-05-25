"""
OCR Text Parser - Segments OCR text files into logical paragraphs.
Handles multiple ProQuest OCR formats.
Supports Tesseract hOCR for bounding box extraction.
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Paragraph:
    doc_id: str
    para_id: str
    paragraph_index: int
    page_number: int
    text: str
    bbox: Optional[dict] = field(default=None)


MIN_PARAGRAPH_CHARS = 80

PROQUEST_BOUNDARY_BOOKS = [
    "NORRIS_1689_0_Reason-and-Religion_0",
    "NORRIS_1688_0_The-Theory-and-Regulation-of-Love_0",
]

MULTI_SECTION_BOOKS = {}

# For each book: offset and divisor
# Formula: pdf_page = (ocr_page - offset) // divisor + 1
# Special first-page overrides handle irregular front matter
BOOK_PAGE_CONFIG = {
    "NORRIS_1687_0_A-Collection-of-Miscellanies_0":        {"anchors": [(1, 6), (25,15),(81, 38), (455,188),(467, 194)]},
    "NORRIS_1688_0_The-Theory-and-Regulation-of-Love_0":  {"anchors": [(1, 7), (66, 79), (243, 132)]},
    "NORRIS_1689_0_Reason-and-Religion_0":                 {"offset": -16, "divisor": 2},
    "NORRIS_1690_0_Reflections-upon-the-Conduct-of-Human-Life_0": {"offset": -4, "divisor": 2},
    "NORRIS_1692_0_Two-Treatises-concerning-the-Divine-Light_0":  {"anchors": [(1, 1), (17, 5), (55, 11), (105, 28)]},
    "NORRIS_1694_0_Spiritual-Counsel-or-The-Fathers-Advice-to-his-Children_0": {"offset": -4, "divisor": 2},
    "NORRIS_1699_0_Practical-Discourses-upon-the-Beatitudes-of-our-Lord-and-Savious-Jesus-Christ_0":  {"anchors": [(1,8),(9,14),(13,16), (189, 123), (203,131)]},
}

# Maximum PDF page count per book â€” paragraphs beyond this are dropped
PDF_PAGE_CAPS = {
    "NORRIS_1687_0_A-Collection-of-Miscellanies_0": 194,
    "NORRIS_1688_0_The-Theory-and-Regulation-of-Love_0": 132,
    "NORRIS_1689_0_Reason-and-Religion_0": 141,
    "NORRIS_1690_0_Reflections-upon-the-Conduct-of-Human-Life_0": 102,
    "NORRIS_1692_0_Two-Treatises-concerning-the-Divine-Light_0": 29,
    "NORRIS_1694_0_Spiritual-Counsel-or-The-Fathers-Advice-to-his-Children_0": 73,
    "NORRIS_1699_0_Practical-Discourses-upon-the-Beatitudes-of-our-Lord-and-Savious-Jesus-Christ_0": 168,
}

# Books where OCR page numbers restart mid-file (stop at restart)
SINGLE_SECTION_BOOKS = {
    "NORRIS_1692_0_Two-Treatises-concerning-the-Divine-Light_0",
}


def ocr_page_to_pdf_page(ocr_page, doc_id=""):
    config = BOOK_PAGE_CONFIG.get(doc_id, {"offset": 0, "divisor": 1})

    # Anchor-based piecewise linear mapping
    if "anchors" in config:
        anchors = sorted(config["anchors"], key=lambda a: a[0])
        if ocr_page <= anchors[0][0]:
            return anchors[0][1]
        if ocr_page >= anchors[-1][0]:
            return anchors[-1][1]
        for i in range(len(anchors) - 1):
            o0, p0 = anchors[i]
            o1, p1 = anchors[i+1]
            if o0 <= ocr_page <= o1:
                return p0 + (ocr_page - o0) * (p1 - p0) // (o1 - o0)
        return anchors[-1][1]

    offset = config["offset"]
    divisor = config["divisor"]
    first_pdf_page = config.get("first_pdf_page", None)

    if ocr_page == 1 and first_pdf_page is not None:
        return first_pdf_page

    pdf_page = (ocr_page - offset) // divisor + 1
    return max(1, pdf_page)


def is_blank(line):
    return line.strip() == ""


def is_proquest_line(line):
    s = line.strip()
    return bool(
        re.search(r'ProQuest\s+LLC', s, re.IGNORECASE) or
        re.search(r'Books\s+Online.*Copyright', s, re.IGNORECASE) or
        re.search(r'Early\s+English\s+Books\s+Online', s, re.IGNORECASE)
    )


def detect_page_marker(line, use_proquest_boundary=False):
    s = line.strip()
    if re.match(r"^[_\-]{5,}$", s):
        return True, None
    m = re.match(r"^Page\s+(\d+)$", s, re.IGNORECASE)
    if m:
        return True, int(m.group(1))
    m = re.match(r"^\((\d+)\)$", s)
    if m:
        return True, int(m.group(1))
    m = re.match(r"^\[(\d+)\]$", s)
    if m:
        return True, int(m.group(1))
    if re.match(r"^Unnumbered\s+page$", s, re.IGNORECASE):
        return True, None
    if use_proquest_boundary and is_proquest_line(line):
        return True, None
    return False, None


def find_header_end(lines):
    for i, line in enumerate(lines):
        if re.match(r"^Full text:", line.strip(), re.IGNORECASE):
            return i + 1
    return 0


def detect_book_format(lines, doc_id):
    for known in PROQUEST_BOUNDARY_BOOKS:
        if known in doc_id:
            return 'proquest_boundary'
    page_n_count = 0
    proquest_count = 0
    for line in lines[:500]:
        if re.match(r"^Page\s+\d+$", line.strip(), re.IGNORECASE):
            page_n_count += 1
        if is_proquest_line(line):
            proquest_count += 1
    if page_n_count == 0 and proquest_count > 3:
        return 'proquest_boundary'
    return 'standard'


def parse_ocr_file(filepath, doc_id):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    book_format = detect_book_format(lines, doc_id)
    use_proquest_boundary = (book_format == 'proquest_boundary')

    paragraphs = []
    current_pdf_page = 1
    current_block = []
    para_index = [0]
    page_counter = [0]
    max_page = PDF_PAGE_CAPS.get(doc_id, 9999)
    is_single_section = doc_id in SINGLE_SECTION_BOOKS
    stop_indexing = [False]

    header_end_idx = find_header_end(lines)

    def flush_block():
        if stop_indexing[0]:
            current_block.clear()
            return
        text = " ".join(current_block).strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"- ([a-z])", r"\1", text)
        current_block.clear()
        if len(text) < MIN_PARAGRAPH_CHARS:
            return
        if text.startswith("http") or "ProQuest" in text or "Copyright" in text:
            return
        AD_PATTERNS = [
            "Books Printed for",
            "Sold by Sam. Manship",
            "Theory and Regulation of Love",
            "Letters Philosophical and Moral",
            "Moral Essay, in Two Parts",
            "Price 2 s",
            "Price 1 s",
        ]
        if any(p in text for p in AD_PATTERNS):
            return
        if "Send your suggestions" in text or "Webmaster" in text:
            return
        if current_pdf_page > max_page:
            return
        para_id = "{}_p{:05d}".format(doc_id, para_index[0])
        paragraphs.append(Paragraph(
            doc_id=doc_id,
            para_id=para_id,
            paragraph_index=para_index[0],
            page_number=current_pdf_page,
            text=text,
        ))
        para_index[0] += 1

    for raw_line in lines[header_end_idx:]:
        if stop_indexing[0]:
            break

        line = raw_line.rstrip("\n\r")

        if line.strip().startswith("http"):
            continue
        if is_proquest_line(line) and not use_proquest_boundary:
            continue

        is_marker, ocr_page = detect_page_marker(line, use_proquest_boundary)
        if is_marker:
            if current_block:
                flush_block()
            if ocr_page is not None:
                new_pdf_page = ocr_page_to_pdf_page(ocr_page, doc_id)
                # Detect section restart: page goes backwards â†’ stop
                if is_single_section and current_pdf_page > 5 and new_pdf_page < current_pdf_page - 3:
                    stop_indexing[0] = True
                    break
                current_pdf_page = new_pdf_page
            elif use_proquest_boundary:
                page_counter[0] += 1
                current_pdf_page = page_counter[0]
            continue

        if is_blank(line):
            if current_block:
                flush_block()
            continue

        current_block.append(line.strip())

    if current_block:
        flush_block()

    return paragraphs


def extract_bbox_for_paragraphs(pdf_path, paragraphs, doc_id):
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image
    except ImportError:
        print("  [bbox] pytesseract/pdf2image not available, skipping bbox extraction")
        return

    if not os.path.exists(pdf_path):
        print(f"  [bbox] PDF not found: {pdf_path}")
        return

    by_page = {}
    for para in paragraphs:
        by_page.setdefault(para.page_number, []).append(para)

    print(f"  [bbox] Extracting bounding boxes for {len(by_page)} pages...")

    for page_num, page_paras in by_page.items():
        try:
            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=150)
            if not images:
                continue
            img = images[0]
            page_w, page_h = img.size
            hocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='eng')
            ocr_words = []
            n = len(hocr_data['text'])
            for i in range(n):
                word = hocr_data['text'][i].strip()
                if not word:
                    continue
                x = hocr_data['left'][i]
                y = hocr_data['top'][i]
                w = hocr_data['width'][i]
                h = hocr_data['height'][i]
                ocr_words.append((word.lower(), x, y, x + w, y + h))
            for para in page_paras:
                para_words = re.findall(r'\b\w+\b', para.text.lower())
                if not para_words:
                    continue
                search_words = para_words[:3]
                best_match_idx = -1
                for i in range(len(ocr_words) - len(search_words) + 1):
                    match = all(ocr_words[i + j][0] == search_words[j] for j in range(len(search_words)))
                    if match:
                        best_match_idx = i
                        break
                if best_match_idx >= 0:
                    end_words = para_words[-3:]
                    end_idx = best_match_idx
                    for i in range(best_match_idx, len(ocr_words) - len(end_words) + 1):
                        match = all(ocr_words[i + j][0] == end_words[j] for j in range(len(end_words)))
                        if match:
                            end_idx = i + len(end_words) - 1
                            break
                    x0 = min(ocr_words[k][1] for k in range(best_match_idx, end_idx + 1))
                    y0 = min(ocr_words[k][2] for k in range(best_match_idx, end_idx + 1))
                    x1 = max(ocr_words[k][3] for k in range(best_match_idx, end_idx + 1))
                    y1 = max(ocr_words[k][4] for k in range(best_match_idx, end_idx + 1))
                    para.bbox = {"x0": x0 / page_w, "y0": y0 / page_h, "x1": x1 / page_w, "y1": y1 / page_h}
        except Exception as e:
            print(f"  [bbox] Error on page {page_num}: {e}")
            continue

    matched = sum(1 for p in paragraphs if p.bbox is not None)
    print(f"  [bbox] Matched {matched}/{len(paragraphs)} paragraphs with bounding boxes")


def parse_all_ocr_files(ocr_dir):
    results = {}
    for fname in sorted(os.listdir(ocr_dir)):
        if not fname.lower().endswith(".txt"):
            continue
        doc_id = os.path.splitext(fname)[0].rstrip(".")
        filepath = os.path.join(ocr_dir, fname)
        paragraphs = parse_ocr_file(filepath, doc_id)
        results[doc_id] = paragraphs
        print("  Parsed '{}' -> {} paragraphs".format(fname, len(paragraphs)))
    return results





























