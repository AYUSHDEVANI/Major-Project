import fitz  # PyMuPDF
import os
import re
import uuid
import logging
from typing import List, Dict
from datetime import datetime, timezone
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, PayloadSchemaType

from app.core.config import settings
from app.core.db import qdrant_client
from app.rag.embeddings import get_embeddings_model

logger = logging.getLogger(__name__)

# --- Metadata Extraction Helpers ---

def extract_section_title(text: str) -> str:
    """Try to extract a section header from the beginning of a text block."""
    lines = text.strip().split("\n")
    for line in lines[:3]:  # Check first 3 lines
        stripped = line.strip()
        # Match patterns like "3.2 Die-Head Replacement" or "CHAPTER 5: MAINTENANCE"
        if re.match(r'^(\d+\.?\d*\s+|CHAPTER\s+|SECTION\s+|PART\s+)', stripped, re.IGNORECASE):
            return stripped[:120]
        # Short uppercase lines are likely headers
        if stripped.isupper() and 3 < len(stripped) < 80:
            return stripped
    return ""

def classify_content_type(text: str) -> str:
    """Classify a chunk as procedure, specification, warning, or general."""
    lower = text.lower()
    if any(kw in lower for kw in ["warning", "caution", "danger", "do not", "hazard"]):
        return "warning"
    if any(kw in lower for kw in ["step ", "1.", "2.", "3.", "procedure", "install", "remove", "replace", "tighten", "loosen"]):
        return "procedure"
    if any(kw in lower for kw in ["torque", "pressure", "voltage", "specification", "rating", "capacity", "dimension"]):
        return "specification"
    return "general"

def extract_machine_id(text: str, filename: str) -> str:
    """Try to identify a machine model/ID from text or filename."""
    # Check for common industrial naming patterns in the text
    patterns = [
        r'(?:Model|Part|Unit|Machine)\s*(?:No\.?|Number|#)?\s*[:.]?\s*([A-Z0-9][\w\-]{2,20})',
        r'\b([A-Z]{2,5}[\-\s]?\d{3,6}[A-Za-z]?)\b',  # e.g., REX-3000, AB-1234
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    # Fallback: use filename without extension
    base = os.path.splitext(filename)[0]
    return base[:50]


# --- Collection Management ---

def ensure_collection_exists():
    """Create the Qdrant collection with dynamic dimensions and payload indexes."""
    collections = qdrant_client.get_collections().collections
    exists = any(c.name == settings.COLLECTION_NAME for c in collections)
    
    if not exists:
        dim = settings.EMBEDDING_DIM
        logger.info(f"Creating Qdrant collection '{settings.COLLECTION_NAME}' with dim={dim}")
        
        qdrant_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        
        # Create payload indexes for filtered search (including company_id for multi-tenancy)
        for field in ["machine_id", "content_type", "source", "company_id"]:
            qdrant_client.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD if field != "company_id" else PayloadSchemaType.INTEGER
            )
        logger.info("Payload indexes created for: machine_id, content_type, source, company_id")


# --- PDF Processing ---

async def process_pdf(file_path: str) -> List[Dict]:
    """Extract text from PDF with page-level metadata."""
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
    
    doc.close()
    return text_content


# --- Chunking & Storage ---

async def chunk_and_store(file: UploadFile, company_id: int = 0):
    """Process PDF: extract → chunk → embed → store in Qdrant with enriched metadata."""
    # Save temp file
    temp_path = f"data/{file.filename}"
    os.makedirs("data", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Extract text
    content_list = await process_pdf(temp_path)
    
    # Improved chunking: smaller chunks with more overlap to preserve procedure steps
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],  # Prefer paragraph → sentence breaks
        keep_separator=True
    )
    
    points = []
    
    ensure_collection_exists()
    embedding_model = get_embeddings_model()

    for item in content_list:
        text = item["text"]
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            continue

        # Batch embed all chunks from this page
        vectors = embedding_model.embed_documents(chunks)
        
        # Extract page-level metadata once
        page_section = extract_section_title(text)
        page_machine_id = extract_machine_id(text, item["source"])
        
        for i, chunk in enumerate(chunks):
            vector = vectors[i]
            
            # Enriched payload with searchable metadata
            payload = {
                "text": chunk,
                "page": item["page"],
                "source": item["source"],
                "section_title": page_section if page_section else extract_section_title(chunk),
                "machine_id": page_machine_id,
                "content_type": classify_content_type(chunk),
                "company_id": company_id,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

            points.append(PointStruct(
                id=str(uuid.uuid4()), 
                vector=vector,
                payload=payload
            ))

    # Upsert to Qdrant
    if points:
        # Batch upsert in groups of 100 for large documents
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            qdrant_client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=batch
            )
        
    logger.info(f"Ingested {len(points)} chunks from {file.filename}")
    return {
        "message": f"Successfully processed {len(points)} chunks from {file.filename}",
        "pages": len(content_list),
        "chunks_stored": len(points),
    }
