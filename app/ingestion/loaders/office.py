import logfire
from unstructured.partition.auto import partition 

def parse_office(file_path: str):
    """
    Parses Office documents (.docx, .pptx) using the Unstructured library.
    Unlike PDFs, these formats are structured and lightweight, so they are processed locally.
    """
    with logfire.span("Parsing Office file", file_path=file_path):
        try:
            elements = partition(filename=file_path)
            full_text = "\n".join([element.text for element in elements])
            if not full_text.strip():
                logfire.warning("Parsed Office file contains no text", file_path=file_path)
            else:       
                logfire.info("Successfully parsed Office file", file_path=file_path)
            return full_text
        except Exception as e:
            logfire.error("Failed to parse Office file", file_path=file_path, error=str(e))
            raise e