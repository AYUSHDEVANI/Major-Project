import hashlib
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings
from cachetools import LRUCache

# LRU cache for text embedding vectors (deterministic for same input)
_text_embedding_cache = LRUCache(maxsize=1024)

class CloudEmbeddings:
    """
    Wrapper for Google Cloud Embeddings to maintain compatibility with 
    the rest of the RAG system while removing local Model/Torch overhead.
    """
    def __init__(self):
        print("🚀 Initializing Google Cloud Embeddings (gemini-embedding-001)...")
        self.client = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY,
            task_type="retrieval_document",
            output_dimensionality=768
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using cloud API and local cache."""
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            # Clean text to ensure cache hits
            clean_text = text.strip()
            cache_key = hashlib.md5(clean_text.encode()).hexdigest()
            
            if cache_key in _text_embedding_cache:
                results[i] = _text_embedding_cache[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(clean_text)

        # Send batch to Google API only for uncached texts
        if uncached_texts:
            try:
                new_vectors = self.client.embed_documents(uncached_texts)
                for j, idx in enumerate(uncached_indices):
                    cache_key = hashlib.md5(uncached_texts[j].encode()).hexdigest()
                    _text_embedding_cache[cache_key] = new_vectors[j]
                    results[idx] = new_vectors[j]
            except Exception as e:
                print(f"❌ Cloud Embedding Error: {e}")
                # Return zero vectors as failsafe if API is down
                for idx in uncached_indices:
                    results[idx] = [0.0] * settings.EMBEDDING_DIM

        return results

    def embed_query(self, text: str) -> List[float]:
        """Convert a single query string to a vector."""
        return self.embed_documents([text])[0]
    
    def embed_image(self, image_path: str) -> List[float]:
        """
        FALLBACK: Google text-embedding-004 does not support images.
        We return a Zero vector to prevent crashes in multimodal code paths.
        Upgrade path: Use Vertex AI 'multimodalembedding' for image support.
        """
        print("⚠️ Warning: Image search is disabled in Cloud-Only mode.")
        return [0.0] * settings.EMBEDDING_DIM

_embedding_model_instance = None

def get_embeddings_model() -> CloudEmbeddings:
    """Lazy-loaded singleton instance for the cloud embedding provider."""
    global _embedding_model_instance
    if _embedding_model_instance is None:
        _embedding_model_instance = CloudEmbeddings()
    return _embedding_model_instance
