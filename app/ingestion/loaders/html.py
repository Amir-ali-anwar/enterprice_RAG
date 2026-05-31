from bs4 import BeautifulSoup
import logfire

def parse_html(file_path: str) -> str:
    """
    Parses HTML files and extracts text content.
    """
    with logfire.span("Parsing HTML file", file_path=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            # Extract text from HTML
            text = soup.get_text(separator='\n', strip=True)
            logfire.info("Successfully parsed HTML file", file_path=file_path)
            return text
        except Exception as e:
            logfire.error("Failed to parse HTML file", file_path=file_path, error=str(e))
            raise e