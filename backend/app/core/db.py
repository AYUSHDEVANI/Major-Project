from qdrant_client import QdrantClient
from app.core.config import settings

def get_qdrant_client() -> QdrantClient:
    """
    Returns a QdrantClient instance based on settings.
    """
    if settings.QDRANT_MODE == "local":
        # Ensure directory exists? QdrantClient handles it mostly, 
        # but let's be safe if it's a path
        return QdrantClient(path=settings.QDRANT_PATH)
    else:
        return QdrantClient(url=settings.QDRANT_URL)

# Global instance
qdrant_client = get_qdrant_client()
