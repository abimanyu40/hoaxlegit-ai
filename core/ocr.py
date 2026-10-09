from PIL import Image
import pytesseract


def extract_text_from_image(image_path: str, lang: str = "ind+eng") -> str:
    """
    Extract text from an image/message screenshot.
    Requires tesseract-ocr installed on the system, plus the Indonesian language pack.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed. On Ubuntu/WSL: sudo apt install tesseract-ocr tesseract-ocr-ind"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to read image: {e}")
