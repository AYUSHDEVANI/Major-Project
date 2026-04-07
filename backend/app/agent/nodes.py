import asyncio
import base64
import json
import os
from app.agent.state import AgentState
from app.rag.retrieval import search_similar
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings

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

async def generate_repair_guide(image_path: str, context: list) -> dict:
    # 1. Prepare Context String
    context_text = "\n".join([f"- {doc['text']} (Source: {doc['source']})" for doc in context])
    
    # Check if we are using Groq (Text Only for this model)
    is_groq = isinstance(llm, ChatGroq)
    
    print(f"--- CALLING LLM (Groq={is_groq}) ---")

    # 3. Construct Prompt
    prompt = f"""
    You are an expert Industrial Maintenance Assistant. 
    Analyze the retrieved manual context below to determine the repair steps.
    
    Context from Manuals:
    {context_text}
    
    Task:
    1. Identify the machine part and potential failure based on context/user query.
    2. Provide a step-by-step repair guide.
    3. List required tools.
    4. Estimate repair time.

    Output format (JSON only):
    {{
        "machine_part": "Name of Part",
        "failure_type": "Type of Failure",
        "repair_steps": ["Step 1", "Step 2", ...],
        "tools_required": ["Tool 1", "Tool 2", ...],
        "estimated_time_minutes": 60
    }}
    """
    
    content_blocks = [{"type": "text", "text": prompt}]
    
    # Only add image if NOT Groq (since Llama 3.3 is text-only here)
    if not is_groq:
         base64_image = encode_image(image_path)
         content_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
         })
    else:
        # For Groq text-only, we append a note about the image
        prompt += "\n\nNote: Visual analysis is disabled (Text-Only Mode). Rely on the Manual Context."
        content_blocks = [{"type": "text", "text": prompt}]

    message = HumanMessage(content=content_blocks)
    
    # 4. Invoke LLM
    try:
        response = await llm.ainvoke([message])
        content = response.content
        
        # Debug Logging
        print(f"DEBUG: RAW LLM OUTPUT:\n{content}\n----------------")

        # Robust JSON Cleanup
        content = content.strip()
        analysis = {}
        try:
            # Text Cleaning: Remove markdown code blocks
            import re
            text = content.replace("```json", "").replace("```", "").strip()
            
            # 2. Aggressive JSON Cleanup
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            
            analysis = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Error generating repair guide: {e}")
            # Fallback for the user's specific case or standard failure
            analysis = {
                 "machine_part": "Partial Analysis Failed",
                 "failure_type": "AI Parsing Error",
                 "repair_steps": [
                     "The AI generated a response but it contained syntax errors.",
                     "This often happens when the image is unclear or not related to the manual.",
                     f"Raw Error: {str(e)[:50]}..."
                 ],
                 "tools_required": ["Manual Inspection"],
                 "estimated_time_minutes": 60
            }
        except Exception as e:
             print(f"General Error generating repair guide: {e}")
             analysis = {
                 "machine_part": "Error",
                 "failure_type": "System Error",
                 "repair_steps": ["Ensure backend is running correctly."],
                 "tools_required": [],
                 "estimated_time_minutes": 0
             }
        return analysis
        
    except Exception as e:
        print(f"Error generating repair guide: {e}")
        # Fallback to safe default just in case of parsing error
        return {
            "machine_part": "Unknown Part (AI Error)",
            "failure_type": "Analysis Failed",
            "repair_steps": ["Consult manual manually.", f"Error: {str(e)}", "Check backend console for raw output."],
            "tools_required": [],
            "estimated_time_minutes": 0
        }

async def retrieve_node(state: AgentState):
    print("--- RETRIEVING DOCUMENTS (SMART HYBRID) ---")
    query_text = state.get("query_text", "")
    image_path = state.get("image_path")
    
    search_query = query_text
    
    # 1. Vision-Based Captioning (If image exists but no text)
    if image_path and not search_query:
        print("--- GENERATING SEARCH QUERY FROM IMAGE ---")
        try:
            # Ask Gemini to describe the part for searching
            base64_image = encode_image(image_path)
            prompt = "Identify this machine part and provide 3-5 keywords to search for it in a technical manual. Return only the keywords."
            
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ])
            
            response = await llm.ainvoke([message])
            search_query = response.content.strip()
            print(f"Generated Query: {search_query}")
        except Exception as e:
            print(f"Error generating query: {e}")
            search_query = "industrial machine repair manual"

    # 2. Perform Search (Visual + Text)
    # If we have an image, we use it for visual similarity AND use the generated text for semantic match
    # For now, we pass the image_path to search_similar to use visual embedding
    
    # Fallback
    if not search_query:
        search_query = "machine maintenance"

    # We use the text query for now, but we COULD also pass query_image_path 
    # if our Qdrant setup supports pure vector search well.
    # Let's use the Image Path to get a visual vector!
    
    docs = await search_similar(
        query_text=search_query if not image_path else None, # Prefer image vector if available, or hybrid?
        # Actually, let's try to search by Image Vector primarily if image is there
        # But commonly manuals are text. Matching Image-Vector to Text-Vector (CLIP) is powerful.
        query_image_path=image_path, 
        top_k=3
    )
    
    # If visual search yields nothing (threshold?), fallback to text
    if not docs and search_query:
        print("Visual search low confidence/empty, trying text search...")
        docs = await search_similar(query_text=search_query, top_k=3)
        
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
        # Handle cases where LLM returns "60 mins" or string "60"
        raw_time = str(analysis.get("estimated_time_minutes", 60))
        import re
        # Extract first number found
        time_matches = re.findall(r'\d+', raw_time)
        if time_matches:
            time_minutes = int(time_matches[0])
        else:
            time_minutes = 60
    except:
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
    
    # --- SAVE TO DB ---
    try:
        from app.core.sql_db import SessionLocal
        from app.models.history import RepairLog
        import json
        
        db = SessionLocal()
        
        log_entry = RepairLog(
            image_filename=os.path.basename(image_path) if image_path else "manual_upload",
            query_text=query_text,
            machine_part=analysis.get("machine_part"),
            failure_type=analysis.get("failure_type"),
            repair_steps=analysis.get("repair_steps", []), # SQLAlchemy handles JSON
            tools_required=analysis.get("tools_required", []),
            estimated_time_minutes=time_minutes,
            traditional_time_minutes=traditional_time_minutes,
            savings_usd=round(money_saved, 2)
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        print(f"Saved Repair Log ID: {log_entry.id}")
        db.close()
        
    except Exception as e:
        print(f"Error saving to DB: {e}")
    
    
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
    import random
    ticket_id = f"INC-{random.randint(10000, 99999)}"
    
    erp_response = {
        "ticket_id": ticket_id,
        "status": "Created",
        "system": "SAP S/4HANA (Mock)"
    }
    
    print(f"SUCCESS: Created Ticket {ticket_id} in SAP.")
    
    return {"erp_result": erp_response}
