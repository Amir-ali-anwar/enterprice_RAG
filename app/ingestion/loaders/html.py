from bs4 import BeautifulSoup
import logfire

def parse_html(file_path: str):
    """
    Parses HTML files.
    """
    with logfire.span("Parsing HTML file", file_path=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            logfire.info("Successfully parsed HTML file", file_path=file_path)
            return soup
        except Exception as e:
            logfire.error("Failed to parse HTML file", file_path=file_path, error=str(e))
            raise e