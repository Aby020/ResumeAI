import pdfplumber

try:
    import easyocr
except ImportError:
    easyocr = None


def extract_pdf_text(pdf_path: str) -> str:
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def extract_image_text(image_path: str) -> str:
    if easyocr is None:
        return ""

    reader = easyocr.Reader(["en"], gpu=False)

    result = reader.readtext(image_path, detail=0)

    return "\n".join(result)


def extract_text(file_path: str) -> str:
    file_path = file_path.lower()

    if file_path.endswith(".pdf"):
        return extract_pdf_text(file_path)

    if file_path.endswith((".png", ".jpg", ".jpeg")):
        return extract_image_text(file_path)

    return ""
