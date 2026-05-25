"""
rename_pdfs.py - Renames the Norris PDF files to match their OCR doc_id counterparts.

Run this ONCE from inside your doc_retrieval_system folder:
    python scripts/rename_pdfs.py

It reads PDFs from data/pdfs/ and renames them so the backend can match
each PDF to its OCR file by doc_id.
"""

import os
import shutil

# Mapping: original PDF filename → new name (doc_id + .pdf)
RENAME_MAP = {
    "Norris A collection of miscellanies.pdf":
        "NORRIS_1687_0_A-Collection-of-Miscellanies_0.pdf",

    "Norris The_theory_and_regulation_of_love.pdf":
        "NORRIS_1688_0_The-Theory-and-Regulation-of-Love_0.pdf",

    "Norris Reason_and_religion,_or,_The_g.pdf":
        "NORRIS_1689_0_Reason-and-Religion_0.pdf",

    "Norris Reflections_upon_the_conduct_o.pdf":
        "NORRIS_1690_0_Reflections-upon-the-Conduct-of-Human-Life_0.pdf",

    "Norris Two Treatises concerning the divine light.pdf":
        "NORRIS_1692_0_Two-Treatises-concerning-the-Divine-Light_0.pdf",

    "Norris Spiritual Counsel or The Fathers Advice to his Children.pdf":
        "NORRIS_1694_0_Spiritual-Counsel-or-The-Fathers-Advice-to-his-Children_0.pdf",

    "Norris Practical_discourses_upon_the_.pdf":
        "NORRIS_1699_0_Practical-Discourses-upon-the-Beatitudes-of-our-Lord-and-Savious-Jesus-Christ_0.pdf",
}

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")


def main():
    pdf_dir = os.path.abspath(PDF_DIR)
    print(f"Looking for PDFs in: {pdf_dir}")

    if not os.path.isdir(pdf_dir):
        print(f"ERROR: folder not found: {pdf_dir}")
        return

    for original, new_name in RENAME_MAP.items():
        src = os.path.join(pdf_dir, original)
        dst = os.path.join(pdf_dir, new_name)

        if os.path.exists(dst):
            print(f"  ✅ Already renamed: {new_name}")
            continue

        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"  ✅ Renamed: {original}\n         → {new_name}")
        else:
            print(f"  ⚠️  Not found (skip): {original}")

    print("\nDone! All PDFs renamed.")


if __name__ == "__main__":
    main()
