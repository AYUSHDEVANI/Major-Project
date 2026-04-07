from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.rag.retrieval import search_similar

router = APIRouter()

class SearchResult(BaseModel):
    score: float
    text: str
    page: Optional[int] = None
    source: Optional[str] = None
    machine_type: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/search/text", response_model=SearchResponse, summary="Search manuals by text")
async def search_by_text(request: TextSearchRequest):
    try:
        results = await search_similar(query_text=request.query, top_k=request.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/image", response_model=SearchResponse, summary="Search manuals by image")
async def search_by_image(
    file: UploadFile = File(...),
    top_k: int = Form(5)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        results = await search_similar(query_image=file, top_k=top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
