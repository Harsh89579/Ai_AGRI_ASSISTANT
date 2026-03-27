import os
import uuid
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path

import httpx
import aiosqlite
import psutil
from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
from rapidfuzz import process, fuzz
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ----------------- Configuration -----------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "chat_orchestrator" / "data" / "agri_knowledge.db")))

# Ensure DB directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ----------------- Models -----------------

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    entities: dict
    source: str
    follow_ups: list[str] = []

class NLUResult(BaseModel):
    intent: str
    crop: str | None = None
    language: str = "hi-en"

# ----------------- App Init -----------------

app = FastAPI(title="AI Agri Assistant - Unified Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Metrics -----------------

REQ_COUNT = Counter("llm_requests_total", "Total LLM requests")
REQ_LATENCY = Histogram("llm_request_latency_seconds", "LLM request latency")

# ----------------- Middleware -----------------

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

# ----------------- Database Logic -----------------

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)
        await db.commit()
    logger.info(f"Database initialized at {DB_PATH}")

@app.on_event("startup")
async def startup_event():
    await init_db()

async def save_to_chat_history(session_id: str, role: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (session_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, message, datetime.now().isoformat())
        )
        await db.commit()

async def get_chat_history(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT role, message, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
    return {"session_id": session_id, "history": [dict(row) for row in rows]}

# ----------------- NLU Logic -----------------

def detect_intent_and_crop(text: str) -> NLUResult:
    t = text.lower()
    intent = "general"
    crop: str | None = None

    if any(w in t for w in ["gehu", "wheat"]): crop = "wheat"
    elif any(w in t for w in ["dhaan", "rice", "chawal"]): crop = "rice"
    elif any(w in t for w in ["tamatar", "tomato"]): crop = "tomato"
    elif any(w in t for w in ["sarson", "mustard"]): crop = "mustard"

    if any(w in t for w in ["khaad", "fertilizer", "urvarak"]): intent = "fertilizer"
    elif any(w in t for w in ["bimari", "rog", "disease", "daag", "spot", "lakshan"]): intent = "disease"
    elif any(w in t for w in ["paani", "sinchai", "irrigation", "water"]): intent = "water"
    elif any(w in t for w in ["daam", "bhav", "mandi", "price"]): intent = "price"

    return NLUResult(intent=intent, crop=crop)

# ----------------- RAG Logic -----------------

async def fuzzy_find_crop(user_crop: str) -> str | None:
    if not user_crop: return None
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT DISTINCT crop_name FROM fertilizer") as cursor:
                all_crops = [row[0] for row in await cursor.fetchall()]
        if not all_crops: return user_crop
        match = process.extractOne(user_crop, all_crops, scorer=fuzz.WRatio)
        if match and match[1] > 70: return str(match[0])
    except Exception as e:
        logger.error(f"Fuzzy find error: {e}")
    return user_crop

async def query_knowledge(intent: str, crop: str | None) -> tuple[str, str]:
    if not crop: return "", "generic"
    crop = await fuzzy_find_crop(crop.lower())
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if intent == "fertilizer":
                async with db.execute("SELECT recommendation FROM fertilizer WHERE LOWER(crop_name) = ?", (crop.lower(),)) as cursor:
                    row = await cursor.fetchone()
                    if row: return row[0], "fertilizer_table"
            elif intent == "disease":
                async with db.execute("SELECT disease_name, recommendation FROM disease WHERE LOWER(crop_name) = ? LIMIT 1", (crop.lower(),)) as cursor:
                    row = await cursor.fetchone()
                    if row: return f"{row[0]}: {row[1]}", "disease_table"
            elif intent == "general":
                async with db.execute("SELECT sowing_month, harvesting_month FROM crop_calendar WHERE LOWER(crop_name) = ?", (crop.lower(),)) as cursor:
                    row = await cursor.fetchone()
                    if row: return f"{crop.capitalize()} aam taur par {row[0]} me boya jata hai aur {row[1]} me kaata jata hai.", "crop_calendar"
    except Exception as e:
        logger.error(f"RAG query error: {e}")
    
    return "", "generic"

# ----------------- LLM Logic -----------------

def build_prompt(user_message, intent, entities, context_data):
    system = "You are an agriculture expert. Reply in simple Hinglish. If unsure, ask ONE concise clarifying question."
    user_block = f"User Query: {user_message}\nIntent: {intent}\nEntities: {entities}\nContext: {context_data}\n"
    constraints = "Constraints:\n- Short, practical steps\n- No hallucination\n- If context insufficient, ask clarification\n- End with ONE next action for farmer"
    return {"system": system, "user": user_block + constraints}

async def call_llm(system, user):
    if not GROQ_API_KEY: return "Maaf karein, AI service abhi available nahi hai (Missed API Key).", []
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.4, "max_tokens": 300
    }
    
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        if resp.status_code != 200: return f"LLM Error: {resp.status_code}", []
        
        content = resp.json()["choices"][0]["message"]["content"].strip()
        try:
            # Try to parse if LLM returns JSON (some logic might expect it)
            data = json.loads(content)
            return data.get("answer", content), data.get("follow_ups", [])
        except:
            return content, []

# ----------------- Formatter Logic -----------------

def format_knowledge_response(intent: str, entities: dict, context_data: str) -> str:
    crop = entities.get("crop")
    if context_data:
        return f"{crop.capitalize() if crop else ''} Jankari: {context_data}"
    if intent == "fertilizer": return "Khaad ki salah ke liye crop ka naam batayein."
    if intent == "disease": return "Fasal ki bimari ke liye lakshan detail me batayein."
    return "Abhi AI service available nahi hai. Kripya apna sawal thoda aur detail me likhein."

# ----------------- Routes -----------------

@app.get("/health")
async def health_check():
    process = psutil.Process(os.getpid())
    return {"status": "ok", "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2)}

@app.get("/api/chat/session")
async def get_all_sessions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT session_id, MIN(timestamp) as start_time FROM chat_history GROUP BY session_id ORDER BY MIN(timestamp) DESC") as cursor:
            rows = await cursor.fetchall()
    return [{"session_id": row["session_id"], "start_time": row["start_time"]} for row in rows]

@app.get("/api/chat/history/{session_id}")
async def proxy_chat_history(session_id: str):
    return await get_chat_history(session_id)

@app.post("/api/chat", response_model=ChatResponse)
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request):
    session_id = req.session_id or str(uuid.uuid4())
    user_message = req.message.strip()
    trace_id = request.state.trace_id
    
    # 1. NLU
    nlu = detect_intent_and_crop(user_message)
    intent, entities = nlu.intent, {"crop": nlu.crop}
    
    # 2. RAG
    context_data, rag_source = await query_knowledge(intent, nlu.crop)
    
    # 3. LLM/Response
    follow_ups = []
    if rag_source != "generic":
        final_answer = format_knowledge_response(intent, entities, context_data)
        source = "knowledge_base"
    else:
        # Get history for context
        history_data = await get_chat_history(session_id)
        context_str = "\n".join([f"{h['role']}: {h['message']}" for h in history_data["history"][-6:]])
        
        prompt = build_prompt(user_message, intent, entities, context_str)
        start_time = time.time()
        final_answer, follow_ups = await call_llm(prompt["system"], prompt["user"])
        REQ_LATENCY.observe(time.time() - start_time)
        REQ_COUNT.inc()
        source = "llm"

    # 4. Save history
    await save_to_chat_history(session_id, "user", user_message)
    await save_to_chat_history(session_id, "bot", final_answer)
    
    return ChatResponse(
        session_id=session_id,
        reply=final_answer,
        intent=intent,
        entities=entities,
        source=source,
        follow_ups=follow_ups
    )

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
