import os
import hashlib
import logging
from typing import List, Dict, Optional
from fastapi import UploadFile
from cachetools import TTLCache
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.db import qdrant_client
from app.rag.embeddings import get_embeddings_model
from app.core.sql_db import SessionLocal
from app.models.user import Document

logger = logging.getLogger(__name__)

def _get_deactivated_sources(company_id: int = 0) -> set:
    """Fetch the set of filenames deactivated by admin for a specific company."""
    try:
        db = SessionLocal()
        query = db.query(Document.source).filter(Document.is_active == False)
        if company_id:
            query = query.filter(Document.company_id == company_id)
        deactivated = query.all()
        db.close()
        return {d.source for d in deactivated}
    except Exception:
        return set()

# TTL cache for search results (5-minute expiry, max 100 entries)
_search_cache = TTLCache(maxsize=100, ttl=300)


def _build_company_filter(company_id: int) -> Optional[Filter]:
    """Build a Qdrant filter to restrict search to a specific company."""
    if not company_id:
        return None
    return Filter(
        must=[
            FieldCondition(key="company_id", match=MatchValue(value=company_id))
        ]
    )


def _format_result(hit) -> Dict:
    """Format a single Qdrant search hit into a standardized result dict."""
    return {
        "score": hit.score,
        "text": hit.payload.get("text", ""),
        "page": hit.payload.get("page"),
        "source": hit.payload.get("source"),
        "section_title": hit.payload.get("section_title", ""),
        "machine_id": hit.payload.get("machine_id", "Unknown"),
        "content_type": hit.payload.get("content_type", "general"),
    }


async def search_similar(
    query_text: Optional[str] = None, 
    query_image: Optional[UploadFile] = None,
    query_image_path: Optional[str] = None,
    top_k: int = 5,
    company_id: int = 0,
) -> List[Dict]:
    """
    Hybrid search using Reciprocal Rank Fusion (RRF) when both image and text
    are available. Falls back to single-modality search otherwise.
    All results are filtered by company_id for multi-tenant isolation.
    """
    from app.rag.ingestion import ensure_collection_exists
    ensure_collection_exists()
    
    embedding_model = get_embeddings_model()
    query_filter = _build_company_filter(company_id)
    
    image_vector = None
    text_vector = None

    # 1. Compute Image Vector
    if query_image_path and os.path.exists(query_image_path):
        image_vector = embedding_model.embed_image(query_image_path)
    elif query_image:
        os.makedirs("data/temp", exist_ok=True)
        temp_path = f"data/temp/{query_image.filename}"
        with open(temp_path, "wb") as f:
            content = await query_image.read()
            f.write(content)
        try:
            image_vector = embedding_model.embed_image(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # 2. Compute Text Vector (with cache check)
    if query_text:
        cache_key = hashlib.md5(f"search:{query_text}:{top_k}:{company_id}".encode()).hexdigest()
        if cache_key in _search_cache and not image_vector:
            logger.debug(f"Cache hit for text query: {query_text[:50]}...")
            return _search_cache[cache_key]
        text_vector = embedding_model.embed_query(query_text)
    
    # 3. If neither modality is available, return empty
    if not image_vector and not text_vector:
        return []

    # 4. If BOTH modalities are available → Reciprocal Rank Fusion
    if image_vector and text_vector:
        results = _rrf_hybrid_search(image_vector, text_vector, top_k, query_filter=query_filter)
    elif image_vector:
        results = _single_vector_search(image_vector, top_k, query_filter=query_filter)
    else:
        results = _single_vector_search(text_vector, top_k, query_filter=query_filter)

    # Cache text-only results (image results change per upload, don't cache)
    if query_text and not image_vector:
        _search_cache[cache_key] = results

    # Filter out results from deactivated documents
    deactivated = _get_deactivated_sources(company_id)
    if deactivated:
        results = [r for r in results if r.get("source") not in deactivated]

    return results


def _single_vector_search(vector: List[float], top_k: int, query_filter=None) -> List[Dict]:
    """Standard single-vector cosine search against Qdrant."""
    search_result = qdrant_client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=vector,
        query_filter=query_filter,
        limit=top_k
    ).points

    return [_format_result(hit) for hit in search_result]


def _rrf_hybrid_search(
    image_vector: List[float], 
    text_vector: List[float], 
    top_k: int,
    k: int = 60,
    query_filter=None,
) -> List[Dict]:
    """
    Reciprocal Rank Fusion (RRF) of image and text vector search results.
    
    RRF score = Σ 1/(k + rank) across each result list.
    k=60 is the standard constant from the original RRF paper.
    """
    fetch_count = top_k * 3  # Fetch more candidates for better fusion coverage

    # Pass 1: Image vector search
    image_hits = qdrant_client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=image_vector,
        query_filter=query_filter,
        limit=fetch_count
    ).points

    # Pass 2: Text vector search
    text_hits = qdrant_client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=text_vector,
        query_filter=query_filter,
        limit=fetch_count
    ).points

    # Build lookup of all hits by ID
    all_hits = {}
    for hit in image_hits + text_hits:
        all_hits[hit.id] = hit

    # Compute RRF scores
    rrf_scores = {}
    for rank, hit in enumerate(image_hits):
        rrf_scores[hit.id] = rrf_scores.get(hit.id, 0) + 1.0 / (k + rank + 1)
    for rank, hit in enumerate(text_hits):
        rrf_scores[hit.id] = rrf_scores.get(hit.id, 0) + 1.0 / (k + rank + 1)

    # Sort by fused score descending, take top_k
    ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

    logger.info(
        f"RRF Fusion: {len(image_hits)} image hits + {len(text_hits)} text hits → {len(ranked_ids)} fused results"
    )

    results = []
    for doc_id in ranked_ids:
        hit = all_hits[doc_id]
        result = _format_result(hit)
        result["score"] = rrf_scores[doc_id]  # Override with RRF score
        results.append(result)

    return results
