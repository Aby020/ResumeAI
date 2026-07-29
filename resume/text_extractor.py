import pdfplumber


def extract_pdf_text(pdf_path: str) -> str:
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def extract_text(file_path: str) -> str:
    file_path = file_path.lower()

    if file_path.endswith(".pdf"):
        return extract_pdf_text(file_path)

    return ""