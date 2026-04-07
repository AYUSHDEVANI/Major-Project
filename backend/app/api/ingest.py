from fastapi import APIRouter, UploadFile, File, HTTPException
from app.rag.ingestion import chunk_and_store

router = APIRouter()

@router.post("/ingest", summary="Upload and Ingest PDF Manual")
async def ingest_manual(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        result = await chunk_and_store(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
