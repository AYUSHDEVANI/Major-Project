import os
import uuid
import shutil
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Depends
from fastapi.responses import StreamingResponse
from app.agent.graph import agent_app
from app.core.auth import RoleChecker
from app.models.user import User

router = APIRouter()

# Allow 'engineer' and 'admin' roles to access diagnostic workflows
engineer_role_checker = RoleChecker(["engineer"])

@router.post("/analyze", summary="Analyze Image and Generate Repair Guide")
async def analyze_machine(
    file: UploadFile = File(...),
    notes: str = Form(None),
    current_user: User = Depends(engineer_role_checker)
):
    # Save Image Temporarily
    os.makedirs("data/temp", exist_ok=True)
    file_path = f"data/temp/{file.filename}"
    
    content = await file.read()
    
    # P1.2: Enforce 10MB max image size
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Initial State
    initial_state = {
        "image_path": file_path,
        "query_text": notes,
        "company_id": current_user.company_id,
        "retrieved_docs": [],
        "analysis_result": {},
        "safety_warnings": [],
        "roi_data": {},
        "history_id": None,
        "erp_result": {}
    }
    
    # Generate unique thread ID for LangGraph MemorySaver
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        async def event_generator():
            try:
                # 1. Start event
                yield f"data: {json.dumps({'step': 'starting', 'thread_id': thread_id})}\n\n"
                
                # 2. Accumulate ALL node outputs into a single merged dict
                accumulated_state = dict(initial_state)
                # Pass config to enable checkpointing
                async for step in agent_app.astream(initial_state, config):
                    node_name = list(step.keys())[0]
                    node_output = step[node_name]
                    accumulated_state.update(node_output)
                    yield f"data: {json.dumps({'step': node_name})}\n\n"
                
                # Check if graph halted (due to interrupt_before erp)
                state_snapshot = agent_app.get_state(config)
                if state_snapshot.next:
                    # Paused before ERP (Human-in-the-loop)
                    yield f"data: {json.dumps({'step': 'paused_for_approval', 'result': accumulated_state, 'thread_id': thread_id})}\n\n"
                else:
                    # 3. Final event
                    yield f"data: {json.dumps({'step': 'done', 'result': accumulated_state, 'thread_id': thread_id})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                # P0.3: Cleanup temp file after stream completes
                # We do NOT delete it here if we want the HITL to have access to it later, 
                # but since state holds base64 or pathways, it's safer to keep memory self-contained. 
                pass

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        # Cleanup on outer failure too
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve/{thread_id}", summary="Approve and Resume ERP Ticket Creation")
async def approve_erp_ticket(
    thread_id: str = Path(..., description="The session thread ID"),
    current_user: User = Depends(engineer_role_checker)
):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get current state from memory
    current_state = agent_app.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="Thread is not waiting for approval.")
        
    try:
        # Resume graph execution (invoking None continues from latest breakpoint)
        result = await agent_app.ainvoke(None, config)
        return {"status": "approved", "final_state": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume graph: {str(e)}")


