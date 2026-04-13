from qdrant_client import QdrantClient
from app.core.config import settings

def get_qdrant_client() -> QdrantClient:
    """
    Returns a QdrantClient instance based on settings.
    """
    print(f"--- INITIALIZING QDRANT (Mode: {settings.QDRANT_MODE.upper()}) ---")
    if settings.QDRANT_MODE == "local":
        return QdrantClient(path=settings.QDRANT_PATH)
    elif settings.QDRANT_MODE == "cloud":
        print(f"Connecting to Qdrant Cloud at {settings.QDRANT_URL}")
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=60  # Increased timeout for cloud/remote ingestions
        )
    else:
        # Default to server mode (localhost:6333)
        url = settings.QDRANT_URL or f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        return QdrantClient(url=url, timeout=60)

# Global instance
qdrant_client = get_qdrant_client()
