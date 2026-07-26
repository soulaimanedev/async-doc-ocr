import logging

import pytesseract
from pdf2image import convert_from_path
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log

logger = logging.getLogger("ocr_service.ocr")


class OCRProcessingError(Exception):
    """Raised when OCR extraction fails for any reason."""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def extract_text_from_pdf(file_path: str) -> str:
    """
    Convert each page of the PDF to an image, then run Tesseract OCR
    on each page, joining the results together.
    """
    try:
        pages = convert_from_path(file_path)
    except Exception as exc:
        raise OCRProcessingError(f"Failed to convert PDF to images: {exc}") from exc

    if not pages:
        raise OCRProcessingError("PDF has no pages to process")

    text_parts = []
    for page_number, page_image in enumerate(pages, start=1):
        try:
            page_text = pytesseract.image_to_string(page_image)
            text_parts.append(page_text)
        except Exception as exc:
            raise OCRProcessingError(f"OCR failed on page {page_number}: {exc}") from exc

    return "\n\n".join(text_parts).strip()