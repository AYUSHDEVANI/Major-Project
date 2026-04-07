import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.agent.graph import agent_app

router = APIRouter()

@router.post("/analyze", summary="Analyze Image and Generate Repair Guide")
async def analyze_machine(
    file: UploadFile = File(...),
    notes: str = Form(None)
):
    # Save Image Temporarily
    os.makedirs("data/temp", exist_ok=True)
    file_path = f"data/temp/{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Initial State
    initial_state = {
        "image_path": file_path,
        "query_text": notes,
        "retrieved_docs": [],
        "analysis_result": {},
        "safety_warnings": [],
        "roi_data": {}
    }
    
    try:
        # Run Graph
        result = await agent_app.ainvoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup (optional, keeping for debugging might be good)
        pass # os.remove(file_path)
