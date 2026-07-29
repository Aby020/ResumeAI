import easyocr


reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def extract_text_from_image(image_path):
    """
    Extract text from a job description screenshot.
    """

    try:

        result = reader.readtext(
            image_path,
            detail=0
        )

        return "\n".join(result)

    except Exception as e:

      

        return ""