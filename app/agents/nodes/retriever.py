import logfire
from app.agents.state import AgentState 
from app.services.retrieval.qdrant_service import search_enterprise_knowledge
from app.services.retrieval.ranking_service import rerank_documents

def retriever_node(state:AgentState) -> AgentState:
    """
    Performs vector search and semantic reranking for technical queries.
    """
    query=state['current_query']
    logfire.info(f"Searching Qdrant for: {query}")
    
    #Retrieval from Qdrant
    results=search_enterprise_knowledge(query,limit=15)
    logfire.info(f"Found {len(results)} results for query: {query}")
    
    #Reranking of documents
    reranked_documents=rerank_documents(query,[res['content'] for res in results],top_k=5)
    logfire.info(f"Found {len(reranked_documents)} results for query: {query}")

    formatted_docs =[f"CONTENT: {doc}\n" for doc in reranked_documents]
    
    return AgentState(
        documents=formatted_docs,
        status=f"Found technical context.",  
        plan= state['plan'] + ['context retrieved']
    )