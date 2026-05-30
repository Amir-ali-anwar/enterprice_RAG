import logfire

def parse_text(file_path: str):
    """
    Parses plain text files.
    """
    
    with logfire.span("Parsing text file", file_path=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logfire.info("Successfully parsed text file", file_path=file_path)
            return content
        except Exception as e:
            logfire.error("Failed to parse text file", file_path=file_path, error=str(e))
            raise e