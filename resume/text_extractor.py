import io

import pdfplumber
import requests


def extract_pdf_text(pdf_source):
    text = ""

    # If Cloudinary URL
    if pdf_source.startswith("http"):
        response = requests.get(pdf_source)
        response.raise_for_status()

        pdf_file = io.BytesIO(response.content)

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    # Local file (development)
    else:
        with pdfplumber.open(pdf_source) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    return text


def extract_text(file_source):
    if file_source.lower().endswith(".pdf"):
        return extract_pdf_text(file_source)

    return ""