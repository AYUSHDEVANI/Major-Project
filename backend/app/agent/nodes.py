import asyncio
import base64
import json
import os
import re
import random
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agent.state import AgentState
from app.rag.retrieval import search_similar
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.sql_db import SessionLocal
from app.models.history import RepairLog

# --- LLM INITIALIZATION ---
# Using Gemini 1.5 Flash for multimodal capabilities
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash", 
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
    max_output_tokens=8192,
    timeout=None,
)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

class RepairGuideOutput(BaseModel):
    machine_part: str = Field(description="Name of the machine part identified")
    failure_type: str = Field(description="Type of failure identified")
    repair_steps: List[str] = Field(description="Step-by-step repair guide")
    tools_required: List[str] = Field(description="List of tools required for repair")
    estimated_time_minutes: int = Field(description="Estimated repair time in minutes")

async def generate_repair_guide(image_path: str, context: list) -> dict:
    # 1. Prepare Context String
    context_text = "\n".join([f"- {doc['text']} (Source: {doc['source']})" for doc in context])
    
    # Check if we are using Groq (Text Only for this model)
    is_groq = isinstance(llm, ChatGroq)
    
    print(f"--- CALLING LLM (Groq={is_groq}) ---")

    # 3. Construct Prompts
    prompt_text = f"""
    You are an expert Industrial Maintenance Assistant. 
    Analyze the retrieved manual context below to determine the repair steps.
    
    Context from Manuals:
    {context_text}
    
    Task:
    1. Identify the machine part and potential failure based on context/user query.
    2. Provide a step-by-step repair guide.
    3. List required tools.
    4. Estimate repair time.
    """
    
    # 4. Try LLM Call with Resiliency (Retry + Fallback)
    import logging
    from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
    
    # Helper to call LLM with retry
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def _call_llm_with_retry(model, messages, model_name="LLM"):
        logging.info(f"Attempting structured invocation with {model_name}...")
        structured_llm = model.with_structured_output(RepairGuideOutput)
        return await structured_llm.ainvoke(messages)

    response_model = None

    # First try Primary LLM (Gemini with Vision)
    primary_blocks = [{"type": "text", "text": prompt_text}]
    if image_path:
        base64_image = encode_image(image_path)
        primary_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
        })
    
    try:
        response_model = await _call_llm_with_retry(llm, [HumanMessage(content=primary_blocks)], "Gemini Primary")
    except Exception as e:
        print(f"⚠️ Primary LLM (Gemini) failed after retries: {e}. Falling back to Groq...")
        
        # Fallback to Text-Only Groq model
        fallback_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_retries=2
        )
        
        fallback_prompt = prompt_text + "\n\nNote: Visual analysis is disabled (Text-Only Mode). Rely on the Manual Context."
        fallback_blocks = [{"type": "text", "text": fallback_prompt}]
        
        try:
            response_model = await _call_llm_with_retry(fallback_llm, [HumanMessage(content=fallback_blocks)], "Groq Fallback")
        except Exception as e2:
            print(f"❌ Fallback LLM (Groq) also failed: {e2}")

    # 5. Handle Results or Return Error Defaults
    if response_model:
        return response_model.model_dump()
    else:
        # Failsafe default dictionary if both models fail
        return {
            "machine_part": "Unknown Part (AI Error)",
            "failure_type": "Analysis Failed due to API limits",
            "repair_steps": [
                "1. Manual intervention required.", 
                "2. System APIs are currently overloaded.", 
                "3. Please check physical diagrams."
            ],
            "tools_required": ["Safety gear", "Standard toolkit"],
            "estimated_time_minutes": 60
        }

async def retrieve_node(state: AgentState):
    print("--- RETRIEVING DOCUMENTS (SMART HYBRID + RRF) ---")
    query_text = state.get("query_text", "")
    image_path = state.get("image_path")
    company_id = state.get("company_id", 0)
    
    search_query = query_text
    
    # 1. Vision-Based Captioning: Generate a text query from the image
    #    This gives us a text vector even when the user only uploads an image,
    #    enabling RRF fusion (image vector + generated text vector).
    if image_path:
        print("--- GENERATING SEARCH QUERY FROM IMAGE ---")
        try:
            base64_image = encode_image(image_path)
            prompt = "Identify this machine part and provide 3-5 keywords to search for it in a technical manual. Return only the keywords."
            
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ])
            
            response = await llm.ainvoke([message])
            generated_query = response.content.strip()
            print(f"Generated Query: {generated_query}")
            
            # Combine user text with vision-generated keywords for richer search
            if search_query:
                search_query = f"{search_query} {generated_query}"
            else:
                search_query = generated_query
        except Exception as e:
            print(f"Error generating query from image: {e}")
            if not search_query:
                search_query = "industrial machine repair manual"

    # 2. Fallback text query
    if not search_query:
        search_query = "machine maintenance"

    # 3. Hybrid Search: pass BOTH image path AND text query
    #    search_similar will use RRF fusion when both are available
    docs = await search_similar(
        query_text=search_query,
        query_image_path=image_path, 
        top_k=5,
        company_id=company_id,
    )
    
    print(f"Retrieved {len(docs)} documents via {'RRF hybrid' if image_path else 'text'} search")
    return {"retrieved_docs": docs}

async def generate_node(state: AgentState):
    print("--- GENERATING REPAIR GUIDE ---")
    image_path = state.get("image_path")
    docs = state.get("retrieved_docs")
    
    result = await generate_repair_guide(image_path, docs)
    return {"analysis_result": result}

async def safety_node(state: AgentState):
    print("--- CHECKING SAFETY ---")
    analysis = state.get("analysis_result")
    warnings = []
    
    part = analysis.get("machine_part", "").lower()
    failure = analysis.get("failure_type", "").lower()
    
    # Dynamic rules based on AI output
    if "high voltage" in part or "electric" in part or "wire" in failure:
        warnings.append("Electrical Hazard: Ensure Lockout/Tagout procedures.")
    if "hydraulic" in part or "pressure" in part or "leak" in failure:
        warnings.append("High Pressure Hazard: Depressurize system before disassembly.")
    if "heat" in failure or "thermal" in part:
        warnings.append("Burn Hazard: Allow components to cool down.")
    if not warnings:
        warnings.append("Standard Safety: Wear PPE (Gloves, Glasses).")
        
    return {"safety_warnings": warnings}

async def roi_node(state: AgentState):
    print("--- CALCULATING ROI & SAVING HISTORY ---")
    analysis = state.get("analysis_result")
    image_path = state.get("image_path")
    query_text = state.get("query_text")
    
    # Robust integer parsing
    try:
        raw_time = str(analysis.get("estimated_time_minutes", 60))
        time_matches = re.findall(r'\d+', raw_time)
        time_minutes = int(time_matches[0]) if time_matches else 60
    except (ValueError, TypeError, AttributeError):
        time_minutes = 60
    
    downtime_cost_per_hour = 5000 
    traditional_time_minutes = time_minutes * 2.5 
    
    time_saved_hours = (traditional_time_minutes - time_minutes) / 60
    money_saved = time_saved_hours * downtime_cost_per_hour
    
    roi_data = {
        "traditional_time_minutes": traditional_time_minutes,
        "ai_time_minutes": time_minutes,
        "savings_usd": round(money_saved, 2)
    }
    
    # --- SAVE TO DB (with guaranteed session cleanup) ---
    db = None
    try:
        db = SessionLocal()
        
        log_entry = RepairLog(
            image_filename=os.path.basename(image_path) if image_path else "manual_upload",
            query_text=query_text,
            machine_part=analysis.get("machine_part"),
            failure_type=analysis.get("failure_type"),
            repair_steps=analysis.get("repair_steps", []),
            tools_required=analysis.get("tools_required", []),
            estimated_time_minutes=time_minutes,
            traditional_time_minutes=traditional_time_minutes,
            savings_usd=round(money_saved, 2),
            company_id=state.get("company_id"),
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        print(f"Saved Repair Log ID: {log_entry.id}")
        
    except Exception as e:
        if db:
            db.rollback()
        print(f"Error saving to DB: {e}")
    finally:
        if db:
            db.close()
    
    return {"roi_data": roi_data}

async def erp_node(state: AgentState):
    print("--- CONNECTING TO ERP SYSTEM ---")
    analysis = state.get("analysis_result")
    roi = state.get("roi_data", {})
    
    # Simulate an external API call
    # In a real app, this would use httpx.post("http://sap-api/...")
    
    # Construct the payload
    payload = {
        "machine_part": analysis.get("machine_part"),
        "failure_type": analysis.get("failure_type"),
        "cost_estimate": roi.get("savings_usd", 0.0),
        "description": f"Auto-generated repair guide for {analysis.get('machine_part')}. Steps: {len(analysis.get('repair_steps', []))}"
    }
    
    # Mocking the response directly to avoid self-recursion network issues in dev
    ticket_id = f"INC-{random.randint(10000, 99999)}"
    
    erp_response = {
        "ticket_id": ticket_id,
        "status": "Created",
        "system": "SAP S/4HANA (Mock)"
    }
    
    print(f"SUCCESS: Created Ticket {ticket_id} in SAP.")
    
    return {"erp_result": erp_response}
