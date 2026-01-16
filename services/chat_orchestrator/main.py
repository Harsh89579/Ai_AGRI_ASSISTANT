from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import sqlite3
import uuid
import httpx
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

# ----------------- Service Configuration -----------------

NLU_SERVICE_URL = "http://nlu_llm:8000/analyze"
RAG_SERVICE_URL = "http://rag_service:8000/query"
LLM_SERVICE_URL = "http://llm_service:8000/generate"

SERVICE_API_KEY = "supersecret-service-key"

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

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


@app.on_event("startup")
async def startup_event():
    init_db()

# ----------------- DB Helper -----------------

def _save_to_chat_history_sync(session_id: str, role: str, message: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chat_history (session_id, role, message, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, role, message, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


async def save_to_chat_history(session_id: str, role: str, message: str):
    await run_in_threadpool(
        _save_to_chat_history_sync,
        session_id,
        role,
        message
    )

# ----------------- Pydantic Models -----------------

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    entities: dict

# ----------------- Health -----------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "chat_orchestrator"}

# ----------------- External Service Calls -----------------

async def call_nlu_service(message: str):
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            NLU_SERVICE_URL,
            json={"message": message},
        )
        res.raise_for_status()
        data = res.json()

    return data["intent"], {"crop": data.get("crop")}


async def call_rag_service(intent: str, entities: dict, message: str):
    async with httpx.AsyncClient(timeout=10) as client:
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



async def call_llm_service(message, intent, entities, context_data):
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            LLM_SERVICE_URL,
            headers={"x-api-key": SERVICE_API_KEY},
            json={
                "user_message": message,
                "intent": intent,
                "entities": entities,
                "context_data": context_data
            }
        )
        res.raise_for_status()
        return res.json()["final_answer"]

# ----------------- RAG Fallback -----------------

def rag_fallback_answer(intent: str, entities: dict, context_data: str) -> str:
    crop = entities.get("crop") if isinstance(entities, dict) else None

    if context_data:
        if crop:
            return f"✅ {crop.capitalize()} ke liye jankari:\n{context_data}"
        return f"✅ Jankari:\n{context_data}"

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
async def chat(req: ChatRequest):

    session_id = req.session_id or str(uuid.uuid4())
    user_message = req.message.strip()

    # 1️⃣ NLU
    intent, entities = await call_nlu_service(user_message)

    # 2️⃣ RAG
    context_data, rag_source = await call_rag_service(intent, entities, user_message)


    # 3️⃣ LLM
    
    # CASE 1: REAL RAG HIT
    if rag_source != "generic":
        final_answer = rag_fallback_answer(
            intent=intent,
            entities=entities,
            context_data=context_data
        )
    # CASE 2: RAG MISS → LLM fallback
    else:
        try:
            final_answer = await call_llm_service(
                user_message,
                intent,
                entities,
                context_data=""
            )
        except Exception as e:
            print("⚠️ LLM API failed:", e)
            final_answer = (
                "Is sawal ke liye abhi exact jankari uplabdh nahi hai. "
                "Kripya thoda aur detail batayein."
            )


    # 4️⃣ Save chat history (FAIL-SAFE)
    try:
        await save_to_chat_history(session_id, "user", user_message)
        await save_to_chat_history(session_id, "bot", final_answer)
    except Exception as e:
        print("⚠️ Chat history save failed:", e)

    return ChatResponse(
        session_id=session_id,
        reply=final_answer,
        intent=intent,
        entities=entities
    )

# ----------------- Chat History APIs -----------------

@app.get("/api/chat/session")
async def get_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT session_id, MIN(timestamp)
        FROM chat_history
        GROUP BY session_id
        ORDER BY MIN(timestamp) DESC
    """)
    rows = cur.fetchall()
    conn.close()

    return [
        {"session_id": row[0], "start_time": row[1]}
        for row in rows
    ]


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT role, message, timestamp
        FROM chat_history
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
        (session_id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="Session ID not found")

    return {
        "session_id": session_id,
        "history": [
            {"role": r, "message": m, "timestamp": t}
            for r, m, t in rows
        ]
    }