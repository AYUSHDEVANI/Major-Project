import fitz  # PyMuPDF
import os
from typing import List, Dict
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from app.core.config import settings
from app.core.db import qdrant_client
from app.rag.embeddings import OpenCLIPEmbeddings

# Initialize global clients
# qdrant_client imported from app.core.db
embedding_model = OpenCLIPEmbeddings()

def ensure_collection_exists():
    collections = qdrant_client.get_collections().collections
    exists = any(c.name == settings.COLLECTION_NAME for c in collections)
    
    if not exists:
        # OpenCLIP ViT-B-32 has 512 dimensions
        qdrant_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )

async def process_pdf(file_path: str) -> List[Dict]:
    doc = fitz.open(file_path)
    text_content = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            text_content.append({
                "text": text,
                "page": page_num + 1,
                "source": os.path.basename(file_path)
            })
            
    return text_content

async def chunk_and_store(file: UploadFile):
    # Save temp file
    temp_path = f"data/{file.filename}"
    os.makedirs("data", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Extract text
    content_list = await process_pdf(temp_path)
    
    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    
    points = []
    idx = 0
    
    ensure_collection_exists()

    for item in content_list:
        # Fix: item is a dict with "text" key
        text = item["text"]
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            continue

        # Batch embed
        vectors = embedding_model.embed_documents(chunks)
        
        for i, chunk in enumerate(chunks):
            vector = vectors[i]
            payload = {
                "text": chunk,
                "page": item["page"],
                "source": item["source"],
                "machine_type": "Generic"
            }
            
            # Use UUID for ID to avoid collisions in real app, but int is fine for demo if managed
            import uuid
            point_id = str(uuid.uuid4())

            points.append(PointStruct(
                id=point_id, 
                vector=vector,
                payload=payload
            ))

    # Upsert to Qdrant
    if points:
        qdrant_client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=points
        )
        
    return {"message": f"Successfully processed {len(points)} chunks from {file.filename}"}

