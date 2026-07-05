"""
PDF Processing Module
Uses pdfplumber for layout-aware text extraction.
Falls back to EasyOCR for scanned / image-heavy pages.
"""

import os
import uuid
import json
from typing import Optional, Dict, List

from chunker import build_parent_child_chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF using pdfplumber (respects columns & reading order).
    For pages that yield no text (scanned images), falls back to EasyOCR.

    Returns the full concatenated text or empty string on failure.
    """
    text_parts = []

    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber is required. Install with: pip install pdfplumber")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()

                if page_text and len(page_text.strip()) > 20:
                    text_parts.append(page_text)
                else:
                    # Scanned page — use OCR fallback
                    ocr_text = _ocr_page(page, page_num)
                    if ocr_text:
                        text_parts.append(ocr_text)

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

    return "\n".join(text_parts).strip()


def _ocr_page(page, page_num: int) -> str:
    """
    OCR a single pdfplumber page using EasyOCR.
    Renders the page to an image then runs OCR on it.
    Returns empty string if EasyOCR is not installed.
    """
    try:
        import easyocr
        import numpy as np
    except ImportError:
        print(f"  ⚠️  Page {page_num} has no text. Install easyocr for OCR support.")
        return ""

    try:
        # Render page to PIL image at 150 DPI
        img = page.to_image(resolution=150).original
        img_array = np.array(img)

        # Lazy-init reader (English — extend list for other languages)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        raw_results = reader.readtext(img_array, detail=0)
        # readtext returns list of str when detail=0, but typed as Unknown — cast explicitly
        ocr_text = " ".join(str(r) for r in raw_results)
        print(f"  📷 OCR page {page_num}: {len(ocr_text)} chars")
        return ocr_text
    except Exception as e:
        print(f"  OCR failed on page {page_num}: {e}")
        return ""


def process_pdf_file(pdf_path: str, filename: str) -> Optional[Dict]:
    """
    Full PDF processing pipeline:
        1. Extract text (pdfplumber + OCR fallback)
        2. Semantic parent-child chunking
        3. Attach metadata

    Returns None if no text could be extracted.
    """
    print(f"📄 Extracting text from: {filename}")
    full_text = extract_text_from_pdf(pdf_path)

    if not full_text:
        print(f"No text extracted from {filename}")
        return None

    pdf_id = str(uuid.uuid4())[:16]
    title = filename.replace('.pdf', '')
    file_size = os.path.getsize(pdf_path)

    print(f"✂️  Building semantic chunks for: {title}")
    parents, children = build_parent_child_chunks(
        text=full_text,
        source_id=pdf_id,
        title=title,
        source_type="pdf",
        child_size=150,
        parent_size=1200,
    )

    print(f"  → {len(parents)} parent chunks, {len(children)} child chunks")

    return {
        "title": title,
        "pdf_id": pdf_id,
        "parents": parents,
        "children": children,
        "total_parents": len(parents),
        "total_children": len(children),
        "total_chars": len(full_text),
        "file_size_bytes": file_size,
    }


def save_pdf_json(data: Dict, output_dir: str = "jsons") -> str:
    """Save processed PDF data to a JSON file for archival."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{data['pdf_id']}_{data['title']}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved PDF chunks to: {filepath}")
    return filepath
