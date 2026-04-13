import hashlib
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from cachetools import LRUCache

# LRU cache for embedding vectors
_text_embedding_cache = LRUCache(maxsize=1024)

class LocalEmbeddings:
    """
    Lightweight local embedding provider using all-MiniLM-L6-v2.
    Size: ~80MB, RAM usage: ~150MB.
    This replaces cloud APIs to avoid regional restrictions (403 errors).
    """
    def __init__(self):
        print("🚀 Initializing Local MiniLM Embeddings (all-MiniLM-L6-v2)...")
        # Downloads model once (~80MB), then loads from disk
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using local model and cache."""
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            clean_text = text.strip()
            cache_key = hashlib.md5(clean_text.encode()).hexdigest()
            
            if cache_key in _text_embedding_cache:
                results[i] = _text_embedding_cache[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(clean_text)

        if uncached_texts:
            try:
                # Local inference is fast and free
                new_vectors = self.model.encode(uncached_texts).tolist()
                for j, idx in enumerate(uncached_indices):
                    cache_key = hashlib.md5(uncached_texts[j].encode()).hexdigest()
                    _text_embedding_cache[cache_key] = new_vectors[j]
                    results[idx] = new_vectors[j]
            except Exception as e:
                print(f"❌ Local Embedding Error: {e}")
                for idx in uncached_indices:
                    results[idx] = [0.0] * settings.EMBEDDING_DIM

        return results

    def embed_query(self, text: str) -> List[float]:
        """Convert a single query string to a vector."""
        return self.embed_documents([text])[0]
    
    def embed_image(self, image_path: str) -> Optional[List[float]]:
        """
        MiniLM is text-only. Returns None to signal that image search is unsupported.
        """
        return None

_embedding_model_instance = None

def get_embeddings_model() -> LocalEmbeddings:
    """Lazy-loaded singleton for the local embedding model."""
    global _embedding_model_instance
    if _embedding_model_instance is None:
        _embedding_model_instance = LocalEmbeddings()
    return _embedding_model_instance
