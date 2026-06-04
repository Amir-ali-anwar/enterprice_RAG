import time
import logfire
from flashrank import Ranker, RerankRequest

# Lazy initialization - Ranker is loaded on first use to ensure logfire.configure() has run

_ranker = None

def _get_ranker() -> Ranker:
    """
    Initializes the FlashRank engine lazily. 
    FlashRank uses a local ONNX model (ms-marco-MiniLM-L-6-v2) for ultra-fast reranking.
    """
    global _ranker
    if _ranker is None:
        logfire.info("Initializing FlashRank...")
        try:
            _ranker = Ranker(cache_dir="/tmp/flashrank")
            logfire.info("Flashrank initialized")
        except Exception as e:
           _ranker = Ranker()
           logfire.info("Flashrank not available, using default Ranker")
    return _ranker


def rerank_documents(query: str, documents: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Refines reterival results by re-scoring documents based on query relevance
    using FlashRank cross-encoder model (ms-marco-MiniLM-L-6-v2)
    Why FlashRank? 
    Standard vector search (Cosine Similarity) is fast but mathematically "fuzzy."
    FlashRank uses a Cross-Encoder approach which is much more precise but usually slow.
    FlashRank solves this by using highly optimized, quantized ONNX models locally.

    """
    if not documents:
        return []
    
    start_time = time.time()
    
    try:
        ranker = _get_ranker()
        
        passages = [{"id":str(i) ,"text": doc} for i,doc in enumerate(documents)]
        
        request = RerankRequest(
            query=query,
            passages=passages,
            top_k=top_k,
        )

        response = ranker.rerank(request)

        ranked_docs=[]

        for passage in response[:top_k]:
            ranked_docs.append(passage['text'])

        duration=time.time()-start_time
        logfire.info(f"Flashrank reranked {len(documents)} documents in {duration:.4f} seconds")
        return ranked_docs
    except Exception as e:
        logfire.error(f"Flashrank reranking failed: {e}")
        return documents[:top_k]
        