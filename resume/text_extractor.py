"""
PDF text extraction.

`parse_pdf(bytes)` is the core parser (used by the analysis service so the raw
bytes can be read once for both hashing and parsing). `extract_pdf` /
`extract_pdf_text` / `extract_text` are thin wrappers kept for backward
compatibility with callers that pass a file object.
"""
import io

import pdfplumber


def parse_pdf(data):
    """
    Parse PDF bytes into text plus layout hints.

    Returns:
        {
            "text": extracted text (may be empty),
            "has_text": whether any text was extracted,
            "is_scanned": True when the PDF holds images but no extractable text,
            "page_count": number of pages,
        }
    """
    text = ""
    has_images = False
    page_count = 0

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = pdf.pages
        page_count = len(pages)
        for page in pages:
            if page.images:
                has_images = True
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    text = text.strip()
    has_text = bool(text)

    return {
        "text": text,
        "has_text": has_text,
        "is_scanned": (not has_text) and has_images,
        "page_count": page_count,
    }


def extract_pdf(file_obj):
    """
    Extract text and layout hints from a PDF file object.

    Returns the same shape as `parse_pdf`.
    """
    # Make sure we're at the beginning of the file
    file_obj.open("rb")

    data = file_obj.read()

    file_obj.close()

    return parse_pdf(data)


def extract_pdf_text(file_obj):
    """Plain-text PDF extraction (kept for backward compatibility)."""
    return extract_pdf(file_obj)["text"]


def extract_text(file_obj):
    filename = file_obj.name.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file_obj)

    return ""