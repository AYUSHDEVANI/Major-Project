import os
import shutil
from typing import List, Dict, Optional
from fastapi import UploadFile
from qdrant_client import QdrantClient

from app.core.config import settings
from app.core.db import qdrant_client
from app.rag.embeddings import OpenCLIPEmbeddings

# Initialize global clients (re-using singletons ideally, or imports)
# qdrant_client imported from app.core.db
embedding_model = OpenCLIPEmbeddings()

async def search_similar(
    query_text: Optional[str] = None, 
    query_image: Optional[UploadFile] = None,
    query_image_path: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Search for similar content in Qdrant collection using text, upload file, or local image path.
    """
    query_vector = None

    # 1. Handle Local Image Path (Priority for Agent)
    if query_image_path:
        if os.path.exists(query_image_path):
             query_vector = embedding_model.embed_image(query_image_path)
    
    # 2. Handle Uploaded Image
    elif query_image:
        # Save temp image
        os.makedirs("data/temp", exist_ok=True)
        temp_path = f"data/temp/{query_image.filename}"
        with open(temp_path, "wb") as f:
            content = await query_image.read()
            f.write(content)
            
        try:
            # Embed image
            query_vector = embedding_model.embed_image(temp_path)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    elif query_text:
        # Embed text
        query_vector = embedding_model.embed_query(query_text)
    else:
        return []

    if not query_vector:
        return []

    # Perform search
    # Updated to use query_points for newer qdrant-client versions
    search_result = qdrant_client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    ).points

    results = []
    for hit in search_result:
        results.append({
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "page": hit.payload.get("page"),
            "source": hit.payload.get("source"),
            "machine_type": hit.payload.get("machine_type", "Unknown")
        })

    return results
