import io

import pdfplumber


def extract_pdf_text(file_obj):
    text = ""

    # Make sure we're at the beginning of the file
    file_obj.open("rb")

    pdf_bytes = io.BytesIO(file_obj.read())

    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    file_obj.close()

    return text


def extract_text(file_obj):
    filename = file_obj.name.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file_obj)

    return ""