import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings
from app.services.retrieval.embedding import get_embedding_model, embed_query

client = None


def _get_client() -> QdrantClient:
    global client
    if client is None:
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            check_compatibility=False,
        )
    return client


def search_enterprise_knowledge(query: str, limit: int = 8):
    """
    Performs a high-precision search in the enterprise knowledge base.
    Uses the modern query_points interface.
    """
    try:
        logfire.info("Searching enterprise knowledge base")
        vector = embed_query(query)
        search_result = _get_client().query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )

        results = []

        for res in search_result.points:
            payload = res.payload or {}
            results.append(
                {
                    "content": payload.get("text", ""),
                    "score": res.score,
                    "source": payload.get("source", None),
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                }
            )

        logfire.info(f"Found {len(results)} results for query: {query}")
        return results
    except Exception as e:
        logfire.error(f"Error searching enterprise knowledge base: {e}")
        return []