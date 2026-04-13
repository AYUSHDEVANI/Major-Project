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
from langchain_openai import ChatOpenAI
import httpx

from app.core.config import settings
from app.core.sql_db import SessionLocal
from app.models.history import RepairLog

# --- LLM INITIALIZATION & QUOTA GUARD ---
print("🚀 PATCH APPLIED: Ultra-Fast Direct HTTP Fallback (v3.0)", flush=True)

# Global flag to skip Gemini if it's already exhausted in this run
_GEMINI_EXHAUSTED = False

if not settings.GOOGLE_API_KEY:
    print("⚠️ WARNING: GOOGLE_API_KEY is missing! Gemini will fail.", flush=True)
else:
    print(f"✅ Gemini Key found (Starts with: {settings.GOOGLE_API_KEY[:5]}...)", flush=True)

if not settings.GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY is missing! Stable fallback will fail.", flush=True)
else:
    print(f"✅ Groq Key found (Starts with: {settings.GROQ_API_KEY[:5]}...)", flush=True)

if not settings.OPENROUTER_API_KEY:
    print("⚠️ WARNING: OPENROUTER_API_KEY is missing! Final fallback will fail.", flush=True)
else:
    print(f"✅ OpenRouter Key found (Starts with: {settings.OPENROUTER_API_KEY[:5]}...)", flush=True)

# Using Gemini 1.5 Flash (1,500 requests/day, 15 RPM)
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash", 
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
    max_output_tokens=8192,
    max_retries=0, # FAIL FAST: Crucial to move to OpenRouter immediately
)

# Text-Only Fallback (High Speed & Alternative Quota)
# fallback_llm = ChatGroq(
#     model="llama-3.2-11b-vision-instant",
#     api_key=settings.GROQ_API_KEY,
#     temperature=0,
#     max_retries=2
# )

fallback_llm = ChatOpenAI(
    model_name="google/gemma-3-12b-it:free", # Standardized to stable Gemma 3
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=settings.OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:3000", 
        "X-Title": "Repair Guide System"
    },
    max_retries=0
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

async def call_openrouter_json_direct(prompt: str) -> dict:
    """Ultra-robust direct HTTP call to OpenRouter to bypass library parsing bugs."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Industrial RAG",
                },
                json={
                    "model": "google/gemma-4-31b-it:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "reasoning": {"enabled": True}
                },
                timeout=8.0
            )
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return extract_json_from_text(content)
            elif response.status_code == 429:
                print(f"⚠️ Gemma 3 busy (429). Trying Llama 3.3 70B Fallback...")
                # Secondary Fallback: Meta Llama 3.3 70B (Different Provider)
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Industrial RAG",
                    },
                    json={
                        "model": "meta-llama/llama-3.3-70b-instruct:free",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content']
                    return extract_json_from_text(content)
                elif response.status_code == 429:
                    print(f"⚠️ Llama 3.3 busy. Trying 'openrouter/free' Catch-All...")
                    # FOURTH FALLBACK: The generic free router (Catch-all for any available free model)
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "HTTP-Referer": "http://localhost:3000",
                            "X-Title": "Industrial RAG",
                        },
                        json={
                            "model": "openrouter/free", # Automatically routes to ANY available free model
                            "messages": [{"role": "user", "content": prompt}],
                        },
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        content = response.json()['choices'][0]['message']['content']
                        return extract_json_from_text(content)
            
            print(f"❌ All OpenRouter free models are currently busy (Status {response.status_code}). Response: {response.text[:100]}", flush=True)
            return {}
    except Exception as e:
        print(f"❌ Direct OpenRouter JSON call failed (Connection Error): {e}", flush=True)
        return {}

async def call_gemini_direct(prompt: str, image_path: str = None) -> dict:
    """Direct HTTP call to Google's Gemini API to bypass LangChain's stubborn retry loops."""
    global _GEMINI_EXHAUSTED
    
    if _GEMINI_EXHAUSTED:
        return {"error": "quota_exhausted"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GOOGLE_API_KEY}"
    
    parts = [{"text": prompt}]
    if image_path:
        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64_img
            }
        })

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"contents": [{"parts": parts}]},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return {"text": text}
            elif response.status_code == 429:
                _GEMINI_EXHAUSTED = True
                print("🚨 Gemini Quota Exhausted (Direct). Switching to fallback mode.")
                return {"error": "quota_exhausted"}
            else:
                return {"error": f"status_{response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": "connection_error", "detail": str(e)}

async def call_groq_direct(prompt: str) -> dict:
    """Direct HTTP call to Groq (Llama 3.3 70B) for ultra-fast, high-quota fallback."""
    if not settings.GROQ_API_KEY:
        return {"error": "no_key"}
    
    # GROQ REQUIREMENT: If using json_object, the word 'JSON' MUST be in the prompt.
    groq_prompt = prompt + "\n\nCRITICAL: Return the response as a VALID JSON object."
    
    # List of models to try in order
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    async with httpx.AsyncClient() as client:
        for model in models:
            try:
                print(f"--- TRYING GROQ MODEL: {model} ---", flush=True)
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": groq_prompt}],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content']
                    return extract_json_from_text(content)
                else:
                    print(f"⚠️ Groq {model} failed (Status {response.status_code}).", flush=True)
            except Exception as e:
                print(f"⚠️ Groq {model} error: {e}", flush=True)
                
    return {}

def extract_json_from_text(text: str) -> dict:
    """Ultra-robust JSON extractor that handles AI reasoning and markdown clutter."""
    if not text:
        return {}
        
    try:
        # 1. Try finding json in markdown blocks (the cleanest way)
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        for block in json_blocks:
            try:
                return json.loads(block)
            except:
                continue

        # 2. Try the furthest apart { and } (for aggressive thinkers)
        # We try to find the largest possible JSON object
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            # Try to fix common AI formatting issues (line breaks in strings)
            potential_json = json_match.group(1).replace('\n', ' ')
            try:
                return json.loads(potential_json)
            except:
                # If first/last fails, try a non-greedy search for the first valid object
                try: 
                    # Cleaning up common trailing commas or bad chars
                    cleaned = re.sub(r',\s*}', '}', potential_json)
                    return json.loads(cleaned)
                except:
                    pass

        # 3. Last resort: print what actually came back for debugging
        print(f"⚠️ Failed to extract JSON. AI Raw Output: {text[:200]}...")
        return {}
    except Exception as e:
        print(f"❌ Error during JSON extraction: {e}")
        return {}

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
    async def _call_llm_with_resiliency(prompt, image):
        # 1. Try Gemini Direct (Primary)
        print(f"--- ATTEMPTING GEMINI DIRECT ---", flush=True)
        res = await call_gemini_direct(prompt, image)
        if "text" in res:
            json_data = extract_json_from_text(res["text"])
            if json_data: return json_data

        # 2. Try Groq Direct (The "Reliable" Fallback)
        print(f"--- FALLING BACK TO GROQ (Llama 3.3) ---", flush=True)
        groq_res = await call_groq_direct(prompt)
        if groq_res: return groq_res
        
        # 3. Last Resort: OpenRouter
        print(f"--- LAST RESORT: OPENROUTER ---", flush=True)
        return await call_openrouter_json_direct(prompt)

    response_model = await _call_llm_with_resiliency(prompt_text, image_path if image_path else None)

    # 5. Handle Results or Return Error Defaults (with STRICT Schema Normalization)
    def normalize_result(data: dict) -> dict:
        """Forces the AI dict into the exact schema expected by the Frontend."""
        
        def to_str_list(val: Any) -> List[str]:
            """Helper to ensure we have a list of strings."""
            if not val:
                return []
            if isinstance(val, str):
                # If they accidentally sent a comma-separated string instead of list
                if ',' in val and '[' not in val:
                    return [s.strip() for s in val.split(',')]
                return [val]
            if not hasattr(val, '__iter__'):
                return [str(val)]
            
            # Extract strings from list, ensuring we don't crash on objects
            return [str(item) for item in val if item is not None]

        # Map common AI variations to strictly underscored keys
        remapped = {
            "machine_part": str(data.get("machine_part") or data.get("machine-part") or data.get("machinePart") or data.get("part") or "Unknown Part"),
            "failure_type": str(data.get("failure_type") or data.get("failure-type") or data.get("failureType") or data.get("failure") or "Unknown Failure"),
            "repair_steps": to_str_list(data.get("repair_steps") or data.get("repair-steps") or data.get("repairSteps") or data.get("steps")),
            "tools_required": to_str_list(data.get("tools_required") or data.get("tools-required") or data.get("toolsRequired") or data.get("tools")),
        }
        
        # Ensure lists are NOT empty (Failsafe)
        if not remapped["repair_steps"]:
            remapped["repair_steps"] = ["Check physical manual for next steps."]
        if not remapped["tools_required"]:
            remapped["tools_required"] = ["Standard technician toolkit"]

        # Clean number conversion for time
        try:
            raw_time = data.get("estimated_time_minutes") or data.get("time") or data.get("duration") or 60
            # Extract first number found in string
            time_match = re.search(r'\d+', str(raw_time))
            remapped["estimated_time_minutes"] = int(time_match.group()) if time_match else 60
        except:
            remapped["estimated_time_minutes"] = 60
            
        return remapped

    # Final normalized result
    final_output = {}
    if response_model and hasattr(response_model, 'model_dump'):
        final_output = normalize_result(response_model.model_dump())
    elif isinstance(response_model, dict) and response_model:
        final_output = normalize_result(response_model)
    else:
        # Failsafe default dictionary if all models fail
        final_output = {
            "machine_part": "System Busy (AI Error)",
            "failure_type": "Analysis Failed due to API limits",
            "repair_steps": ["1. Manual intervention required.", "2. Please check physical diagrams."],
            "tools_required": ["Safety gear"],
            "estimated_time_minutes": 60
        }

    return final_output

async def retrieve_node(state: AgentState):
    print("--- RETRIEVING DOCUMENTS (SMART HYBRID + RRF) ---")
    query_text = state.get("query_text", "")
    image_path = state.get("image_path")
    company_id = state.get("company_id", 0)
    
    search_query = query_text
    
    if image_path:
        try:
            base64_image = encode_image(image_path)
            prompt = "Identify this machine part and provide 3-5 keywords for a technical manual search. Return ONLY the keywords."
            
            if _GEMINI_EXHAUSTED:
                print("⏭️ Gemini exhausted. Skipping vision and using direct fallback...")
                raise Exception("Quota Exhausted")

            print("--- ATTEMPTING GEMINI VISION DIRECT ---")
            res = await call_gemini_direct(prompt, image_path)
            
            if "text" in res:
                generated_query = res["text"].strip()
            else:
                # Direct Fallback to OpenRouter (Direct HTTP)
                print(f"⚠️ Gemini Vision failed. Falling back to OpenRouter...")
                async with httpx.AsyncClient() as client:
                    response_raw = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "HTTP-Referer": "http://localhost:3000",
                            "X-Title": "Industrial RAG",
                        },
                        json={
                            "model": "google/gemma-3-12b-it:free", 
                            "messages": [
                                {"role": "user", "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]}
                            ],
                            "reasoning": {"enabled": True}
                        },
                        timeout=30.0
                    )
                    
                    if response_raw.status_code == 200:
                        data = response_raw.json()
                        generated_query = data['choices'][0]['message']['content'].strip()
                    elif response_raw.status_code == 429:
                        print(f"⚠️ Gemma 3 Vision busy (429). Trying Llama (Text-Only) fallback...")
                        # Triple Fallback: If both vision models fail, try a Llama text query
                        response_raw = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                                "HTTP-Referer": "http://localhost:3000",
                                "X-Title": "Industrial RAG",
                            },
                            json={
                                "model": "meta-llama/llama-3.3-70b-instruct:free",
                                "messages": [{"role": "user", "content": f"Based on this industrial failure context, suggest search keywords: {prompt}"}],
                            },
                            timeout=30.0
                        )
                        if response_raw.status_code == 200:
                            data = response_raw.json()
                            generated_query = data['choices'][0]['message']['content'].strip()
                        else:
                            generated_query = "maintenance"
                    else:
                        print(f"ℹ️ OpenRouter Gemma 3 Vision fallback failed (Code {response_raw.status_code}). Using keyword 'maintenance'.")
                        generated_query = "maintenance"

            print(f"Generated Keywords: {generated_query}")
            search_query = f"{search_query} {generated_query}".strip()
            
        except Exception as e:
            print(f"General Error in query generation: {e}")
            if not search_query:
                search_query = "industrial machine repair"

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
    
    return {"roi_data": roi_data, "history_id": log_entry.id if 'log_entry' in locals() else None}

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
