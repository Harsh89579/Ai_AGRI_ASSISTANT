from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import psutil
from loguru import logger
from .services.orchestrator import process_chat, get_chat_history, get_all_sessions, init_db

app = FastAPI(title="AI Agri Assistant - Unified Backend")

# ---------------- Middlewares ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

# ---------------- App Startup ----------------

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Backend started and DB initialized.")

# ---------------- Pydantic Models ----------------

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    source: str = "unknown"
    follow_ups: list[str] = []

# ---------------- Endpoints ----------------

@app.get("/health", tags=["system"])
async def health_check():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "status": "ok", 
        "service": "unified_backend",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }

@app.get("/api/chat/session")
async def fetch_sessions():
    try:
        return await get_all_sessions()
    except Exception as e:
        logger.error(f"Session fetch error: {e}")
        return []

@app.get("/api/chat/history/{session_id}")
async def fetch_history(session_id: str):
    try:
        history = await get_chat_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    try:
        result = await process_chat(payload.message, payload.session_id)
        return ChatResponse(
            session_id=result["session_id"],
            reply=result["reply"],
            source=result["source"],
            follow_ups=result.get("follow_ups", [])
        )
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        return ChatResponse(
            session_id=payload.session_id or "unknown",
            reply="Kuch dikkat aa gayi hai. Kripya thodi der baad try karein.",
            source="error"
        )

# Redirect root to docs for easy testing
from fastapi.responses import RedirectResponse
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
