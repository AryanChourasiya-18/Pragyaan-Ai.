"""Extracts text from PDFs, falling back to OCR for scanned/image-only pages."""
import os
from typing import List, Tuple

from PyPDF2 import PdfReader


def extract_text_per_page(file_path: str) -> Tuple[List[str], bool]:
    """Returns (list of page texts, whether OCR was used for any page)."""
    reader = PdfReader(file_path)
    pages: List[str] = []
    used_ocr = False

    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if len(text) < 20:
            # Likely a scanned/image page — fall back to OCR.
            ocr_text = _ocr_page(file_path, reader.pages.index(page))
            if ocr_text:
                text = ocr_text
                used_ocr = True
        pages.append(text)

    return pages, used_ocr


def _ocr_page(file_path: str, page_index: int) -> str:
    """OCR a single page image using pdf2image + pytesseract.

    Requires poppler-utils and tesseract-ocr installed on the host/container.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(
            file_path, first_page=page_index + 1, last_page=page_index + 1
        )
        if not images:
            return ""
        return pytesseract.image_to_string(images[0])
    except Exception:
        # OCR dependencies missing or failed — degrade gracefully.
        return ""


def chunk_pages(pages: List[str], chunk_size: int = 900, overlap: int = 150) -> List[dict]:
    """Splits page texts into overlapping chunks for embedding, tagged with page number."""
    chunks = []
    for page_num, text in enumerate(pages, start=1):
        if not text:
            continue
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append({"page": page_num, "text": chunk})
            start = end - overlap
    return chunks
