# PDF text extraction service
# Library: PyMuPDF (imported as fitz)

import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file and return as a single clean string.
    
    Args:
        file_path: path to the PDF file on disk
        
    Returns:
        cleaned text string
        
    Raises:
        ValueError: if PDF appears to be scanned (no extractable text)
    """
    full_text = ""

    with fitz.open(file_path) as doc:
        for page in doc:
            page_text = page.get_text()
            full_text += page_text

    # clean the text
    full_text = full_text.strip()
    full_text = " ".join(full_text.split())

    # check if scanned PDF
    if len(full_text) < 100:
        raise ValueError(
            "This appears to be a scanned PDF. "
            "Text extraction failed. Please upload a digital PDF."
        )

    return full_text