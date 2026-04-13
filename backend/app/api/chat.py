from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio
from typing import Optional, List

from app.core.sql_db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.history import RepairLog
from app.models.chat import ChatSession, ChatMessage
from app.rag.retrieval import search_similar
from app.agent.nodes import llm
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(prefix="/chat", tags=["AI Support Chat"])

@router.get("/sessions")
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all chat sessions for the current user."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at
        } for s in sessions
    ]

@router.get("/sessions/{session_id}")
async def get_chat_history(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full message history for a specific session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp
        } for m in messages
    ]

@router.post("/stream")
async def chat_support(
    message: str = Query(...),
    session_id: Optional[int] = Query(None),
    history_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Streaming chat endpoint with persistence.
    """
    
    # 1. Handle Session
    active_session_id = session_id
    if not active_session_id:
        # Create a new session
        new_session = ChatSession(
            user_id=current_user.id,
            company_id=current_user.company_id,
            title=message[:50] + ("..." if len(message) > 50 else "")
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        active_session_id = new_session.id
    
    # 2. Save User Message
    user_chat_msg = ChatMessage(
        session_id=active_session_id,
        role="user",
        content=message
    )
    db.add(user_chat_msg)
    db.commit()

    async def event_generator():
        try:
            # Send session ID first so frontend can track it
            yield f"data: {json.dumps({'status': 'searching', 'session_id': active_session_id})}\n\n"
            
            # --- MOVE HEAVY RETRIEVAL INSIDE GENERATOR ---
            # 1. Retrieve Context from Manuals (Lazy-loads OpenCLIP inside generator)
            docs = await search_similar(
                query_text=message, 
                top_k=4, 
                company_id=current_user.company_id
            )
            context_text = "\n".join([f"- {d['text']} (Source: {d['source']})" for d in docs])
            
            # 2. Retrieve Specific History Context
            history_context = ""
            if history_id:
                log = db.query(RepairLog).filter(RepairLog.id == history_id, RepairLog.company_id == current_user.company_id).first()
                if log:
                    history_context = f"\nUser is currently referencing this repair history:\n- Part: {log.machine_part}\n- Failure: {log.failure_type}\n- Steps taken: {', '.join(log.repair_steps)}"

            # 3. Construct System Prompt
            full_system_prompt = f"""
            You are an IndustriFix AI Support Assistant. 
            Your goal is to help maintenance engineers and viewers understand technical manuals and repair procedures.
            
            Context from technical manuals:
            {context_text}
            {history_context}
            
            Instructions:
            - Use the provided context to answer accurately.
            - If the user asks about a specific step in the history, offer detailed guidance.
            - If information is missing from context, advise checking with a senior engineer or the physical machine.
            - Be professional, concise, and safety-oriented.
            """

            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=message)
            ]
            
            # --- Robust Streaming with Fallbacks (PRIMARY: Groq) ---
            from app.agent.nodes import groq_llm, fallback_llm
            
            assistant_response = ""
            stream_started = False
            
            # 1. Try Primary (Groq - User Requested)
            try:
                print("🚀 Chat using Groq (Primary)...")
                async for chunk in groq_llm.astream(messages):
                    if chunk.content:
                        stream_started = True
                        assistant_response += chunk.content
                        yield f"data: {json.dumps({'text': chunk.content})}\n\n"
            except Exception as e:
                print(f"⚠️ Groq Chat Stream failed: {e}")

            # 2. Try Fallback 1 (Gemini)
            if not assistant_response:
                try:
                    print("🔄 Falling back to Gemini for chat...")
                    async for chunk in llm.astream(messages):
                        if chunk.content:
                            assistant_response += chunk.content
                            yield f"data: {json.dumps({'text': chunk.content})}\n\n"
                except Exception as e:
                    print(f"⚠️ Gemini Chat Stream failed: {e}")

            # 3. Try Fallback 2 (OpenRouter/Gemma)
            if not assistant_response:
                try:
                    print("🔄 Falling back to OpenRouter for chat...")
                    async for chunk in fallback_llm.astream(messages):
                        if chunk.content:
                            assistant_response += chunk.content
                            yield f"data: {json.dumps({'text': chunk.content})}\n\n"
                except Exception as e:
                    print(f"⚠️ OpenRouter Chat Stream failed: {e}")

            if not assistant_response:
                yield f"data: {json.dumps({'text': 'I am currently experiencing higher traffic than usual. Please try again in a few moments.'})}\n\n"

            # Save Assistant Message to DB
            if assistant_response:
                try:
                    ai_chat_msg = ChatMessage(
                        session_id=active_session_id,
                        role="assistant",
                        content=assistant_response
                    )
                    db.add(ai_chat_msg)
                    db.commit()
                except Exception as db_err:
                    print(f"Error saving AI message: {db_err}")

            yield f"data: {json.dumps({'status': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Support Chat Error: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
