# Loaders package
from .text import parse_text
from .html import parse_html

# PDF loader imported lazily to avoid GCP auth at import time
def load_pdf(file_name: str):
    from .pdf import load_pdf as _load_pdf
    return _load_pdf(file_name)
