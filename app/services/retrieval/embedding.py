"""
Embedding service using Vertex AI.
"""

import logfire
from typing import List
from vertexai.language_models import TextEmbeddingModel

# Lazy initialization
_model = None


def _get_model():
    """Get or create the embedding model lazily."""
    global _model
    if _model is None:
        _model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    return _model


def get_embedding_model():
    """Get the underlying embedding model."""
    return _get_model()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Vertex AI.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (each vector is a list of floats)
    """
    with logfire.span("Embedding texts", count=len(texts)):
        try:
            model = _get_model()

            # Vertex AI has a limit on batch size, process in batches of 250
            batch_size = 250
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                embeddings = model.get_embeddings(batch)
                all_embeddings.extend([e.values for e in embeddings])

            logfire.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logfire.error(f"Embedding failed: {e}")
            raise


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a single query string.

    Args:
        query: Query string to embed

    Returns:
        Embedding vector (list of floats)
    """
    embeddings = embed_texts([query])
    return embeddings[0]
