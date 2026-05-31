import io
import logfire
from pypdf import PdfReader, PdfWriter
from google.cloud import documentai
from app.config import settings

# Lazy initialization - client created only when needed
_client = None

MAX_PAGES_PER_REQUEST = 15


def _get_client():
    """Get or create the Document AI client lazily."""
    global _client
    if _client is None:
        _client = documentai.DocumentProcessorServiceClient()
    return _client

def load_pdf(file_name: str):
    """
    Parses PDF using Google Cloud Document AI.
    Automatically splits large PDFs into 15-page chunks to bypass synchronous API limits.
    """
    
    with logfire.span("Loading PDF", file_name=file_name):
        try:
            reader = PdfReader(file_name)
            total_pages = len(reader.pages)
            logfire.info(f"Total pages in PDF: {total_pages}")

            client = _get_client()
            name = client.processor_path(settings.PROJECT_ID, settings.GCP_DOC_AI_LOCATION, settings.GCP_DOC_AI_PROCESSOR_ID)
            document_chunks = ''
            
            if total_pages <= MAX_PAGES_PER_REQUEST:
                with io.open(file_name, 'rb') as f:
                    image_content = f.read()
                document_chunks = process_chunk(name, image_content)
            else:
                logfire.info(f"PDF exceeds {MAX_PAGES_PER_REQUEST} pages. Splitting into chunks...")

                for i in range(0, total_pages, MAX_PAGES_PER_REQUEST):
                    writer = PdfWriter()
                    chunk_end = min(i + MAX_PAGES_PER_REQUEST, total_pages)
                    for j in range(i, chunk_end):
                        writer.add_page(reader.pages[j])
                    with io.BytesIO() as bytes_stream:
                        writer.write(bytes_stream)
                        chunk_bytes = bytes_stream.getvalue()
                        
                    with logfire.span("Processing PDF chunk", chunk_start=i, chunk_end=chunk_end):
                        chunk_text = process_chunk(name, chunk_bytes)
                        document_chunks += chunk_text + "\n"
                        
            if not document_chunks.strip():
                logfire.warning(f"⚠️ Document AI returned empty text for {file_name}")
            else:
                logfire.info(f"✅ Document AI successfully parsed {len(document_chunks)} characters")

            return document_chunks

        except Exception as e:
            logfire.error(f"❌ Document AI Parse Failed: {e}")
            logfire.info("💡 Ensure the Processor ID is correct and the API is enabled.")
            raise e


                
def process_chunk(name, image_content):
    raw_document = documentai.RawDocument(
        content=image_content,
        mime_type="application/pdf"
    )
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
    )
    client = _get_client()
    response = client.process_document(request=request)
    return response.document.text


# Alias for backwards compatibility
parse_pdf = load_pdf