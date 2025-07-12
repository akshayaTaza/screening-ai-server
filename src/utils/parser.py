import fitz  # PyMuPDF

def extract_text_from_pdf(path):
    with fitz.open(path) as doc:
        return "\n".join([page.get_text() for page in doc]) 