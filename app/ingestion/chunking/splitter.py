from typing import List
import logfire  

def split_text_into_chunks(text: str, chunk_size: int) -> List[str]:    
    """
    Simple semantic-ish chunker that splits by paragraphs.
    Ensures chunks do not exceed the specified size.
    """
    
    with logfire.span("split_text_into_chunks"):
        if not text.strip():
            return []

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:  # +2 for the two newlines
                current_chunk += paragraph + "\n\n"
                
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        valid_chunks = [chunk for chunk in chunks if chunk.strip()]
        logfire.info(f"Split text into {len(valid_chunks)} chunks.")
        return valid_chunks


# Alias for backwards compatibility
def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Alias for split_text_into_chunks."""
    return split_text_into_chunks(text, chunk_size) 
            