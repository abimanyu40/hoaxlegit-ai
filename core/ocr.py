from PIL import Image
import pytesseract


def extract_text_from_image(image_path: str, lang: str = "ind+eng") -> str:
    """
    Extract teks dari gambar/screenshot pesan.
    Butuh tesseract-ocr terinstall di sistem + paket bahasa Indonesia.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract belum terinstall. Di Ubuntu/WSL: sudo apt install tesseract-ocr tesseract-ocr-ind"
        )
    except Exception as e:
        raise RuntimeError(f"Gagal baca gambar: {e}")
