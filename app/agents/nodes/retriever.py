import logfire

from app.agents.state import AgentState
from app.config import settings
from app.services.retrieval.qdrant_service import search_enterprise_knowledge
from app.services.retrieval.ranking_service import rerank_documents


def retriever_node(state: AgentState) -> AgentState:
    """
    Performs vector search and semantic reranking for technical queries.
    """
    query = state["current_query"]
    logfire.info(f"Searching Qdrant for: {query}")

    # Retrieval from Qdrant
    results = search_enterprise_knowledge(query, limit=15)
    logfire.info(f"Found {len(results)} results for query: {query}")

    if settings.ENABLE_RERANK:
        # Reranking of documents (preserves source/score/chunk_id for citations)
        reranked_documents = rerank_documents(query, results, top_k=5)
        logfire.info(f"Found {len(reranked_documents)} results for query: {query}")
    else:
        # Stability-first mode for small instances (e.g. Render starter/free).
        reranked_documents = results[:5]
        logfire.info("Reranking disabled by ENABLE_RERANK, using top vector hits")

    formatted_docs = [
        {
            "content": doc.get("content", ""),
            "source": doc.get("source") or "unknown",
            "score": doc.get("rerank_score", doc.get("score")),
            "chunk_id": doc.get("chunk_id"),
        }
        for doc in reranked_documents
    ]

    return AgentState(
        documents=formatted_docs,
        status="Found technical context.",
        plan=state["plan"] + ["context retrieved"],
    )