from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import aiosqlite
import uuid
import httpx
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
import time

# ----------------- Service Configuration -----------------

import os
NLU_SERVICE_URL = os.getenv("NLU_SERVICE_URL", "http://nlu_llm:8000/analyze")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag_service:8000/query")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm_service:8000/generate")

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "supersecret-service-key")

# ----------------- App Init -----------------

app = FastAPI(title="AI Agri Assistant - Chat Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Database Config -----------------

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "agri_knowledge.db"

# 🔥 IMPORTANT: auto-create folder
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ----------------- DB Init -----------------

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

# ----------------- DB Helper -----------------

async def save_to_chat_history(session_id: str, role: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO chat_history (session_id, role, message, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, message, datetime.now().isoformat())
        )
        await db.commit()
    logger.debug(f"Saved {role} message for session {session_id}")

# ----------------- Middlewares -----------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s")
    return response

# ----------------- Pydantic Models -----------------

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

# ----------------- Health -----------------

import psutil

@app.get("/health")
async def health():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "status": "ok", 
        "service": "chat_orchestrator",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }

# ----------------- External Service Calls -----------------

async def call_nlu_service(message: str, trace_id: str):
    headers = {"X-Trace-ID": trace_id}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        res = await client.post(
            NLU_SERVICE_URL,
            json={"message": message},
        )
        res.raise_for_status()
        data = res.json()

    return data["intent"], {"crop": data.get("crop")}


async def call_rag_service(intent: str, entities: dict, message: str, trace_id: str):
    headers = {"X-Trace-ID": trace_id}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        res = await client.post(
            RAG_SERVICE_URL,
            json={
                "intent": intent,
                "crop": entities.get("crop"),
                "message": message
            },
        )
        res.raise_for_status()
        data = res.json()

    return data.get("context", ""), data.get("source", "generic")



async def call_llm_service(message, intent, entities, context_data, trace_id: str):
    headers = {
        "x-api-key": SERVICE_API_KEY,
        "X-Trace-ID": trace_id
    }
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        res = await client.post(
            LLM_SERVICE_URL,
            json={
                "user_message": message,
                "intent": intent,
                "entities": entities,
                "context_data": context_data
            }
        )
        res.raise_for_status()
        data = res.json()
        return data["final_answer"], data.get("follow_ups", [])

# ----------------- RAG Fallback -----------------

def format_knowledge_response(intent: str, entities: dict, context_data: str) -> str:
    crop = entities.get("crop") if isinstance(entities, dict) else None

    if context_data:
        if crop:
            return f"{crop.capitalize()} ke liye jankari: {context_data}"
        return f"Jankari: {context_data}"

    if intent == "fertilizer":
        return "Khaad ki salah ke liye crop ka naam batayein (jaise gehu, dhaan)."

    if intent == "disease":
        return "Fasal ki bimari ke liye lakshan detail me batayein."

    if intent == "water":
        return "Paani ki matra fasal aur mausam par depend karti hai."

    return (
        "Abhi AI service available nahi hai. "
        "Kripya apna sawal thoda aur detail me likhein."
    )

# ----------------- Chat Endpoint -----------------

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):

    session_id = req.session_id or str(uuid.uuid4())
    user_message = req.message.strip()
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    logger.info(f"[{trace_id}] [{session_id}] Processing message: {user_message[:50]}")

    # Fetch recent history for context
    # Only sending the last few turns to avoid context bloat
    recent_history = []
    context_str = ""
    try:
        if os.path.exists(DB_PATH):
            history_records = await get_chat_history(session_id)
            if history_records and "history" in history_records:
                # Take the last 3 turns
                recent_history = [
                    f"Farmer: {row['message']}\nAI: "
                    for row in history_records["history"][-6:]
                ]
        context_str = "\n".join(recent_history)
    except Exception as e:
        logger.warning(f"[{trace_id}] Could not load history for context: {e}")

    # 1️⃣ NLU
    intent, entities = await call_nlu_service(user_message, trace_id)

    # 2️⃣ RAG
    context_data, rag_source = await call_rag_service(intent, entities, user_message, trace_id)


    # 3️⃣ LLM
    
    # CASE 1: REAL RAG HIT
    if rag_source != "generic":
        final_answer = format_knowledge_response(
            intent=intent,
            entities=entities,
            context_data=context_data
        )
        source = "knowledge_base"
    # CASE 2: RAG MISS → LLM fallback
    else:
        try:
            final_answer, follow_ups = await call_llm_service(
                user_message,
                intent,
                entities,
                context_data=context_str,
                trace_id=trace_id
            )
            source = "llm"
        except Exception as e:
            logger.error(f"[{trace_id}] LLM API failed: {e}")
            final_answer = (
                "Is sawal ke liye abhi exact jankari uplabdh nahi hai. "
                "Kripya thoda aur detail batayein."
            )
            follow_ups = []
            source = "error"


    # 4️⃣ Save chat history (FAIL-SAFE)
    try:
        await save_to_chat_history(session_id, "user", user_message)
        await save_to_chat_history(session_id, "bot", final_answer)
    except Exception as e:
        logger.error(f"Chat history save failed: {e}")

    return ChatResponse(
        session_id=session_id,
        reply=final_answer,
        intent=intent,
        entities=entities,
        source=source,
        follow_ups=follow_ups if 'follow_ups' in locals() else []
    )

# ----------------- Chat History APIs -----------------

@app.get("/api/chat/session")
async def get_all_sessions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT session_id, MIN(timestamp) as start_time
            FROM chat_history
            GROUP BY session_id
            ORDER BY MIN(timestamp) DESC
        """) as cursor:
            rows = await cursor.fetchall()

    return [
        {"session_id": row["session_id"], "start_time": row["start_time"]}
        for row in rows
    ]


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT role, message, timestamp
            FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        logger.warning(f"Session history not found: {session_id}")
        return {"session_id": session_id, "history": []}

    return {
        "session_id": session_id,
        "history": [
            {"role": row["role"], "message": row["message"], "timestamp": row["timestamp"]}
            for row in rows
        ]
    }