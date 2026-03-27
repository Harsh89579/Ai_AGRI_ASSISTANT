import os
import uuid
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from app.models.schemas import ChatRequest, ChatResponse, SessionResponse, ChatHistoryResponse
from app.db.database import init_db, save_to_chat_history, get_chat_history, get_all_sessions
from app.services.nlu_service import detect_intent_and_crop
from app.services.rag_service import query_knowledge
from app.services.llm_service import call_llm, format_knowledge_response

# App Init
app = FastAPI(title="AI Agri Assistant - Unified Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "unified_agri_assistant"}

# ----------------- Chat APIs -----------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    user_message = req.message.strip()
    
    logger.info(f"Session {session_id} | Message: {user_message[:50]}")

    # 1. NLU (Intent detection)
    nlu = detect_intent_and_crop(user_message)
    intent, entities = nlu.intent, {"crop": nlu.crop}

    # 2. RAG (Knowledge base retrieval)
    context_data, rag_source = await query_knowledge(intent, nlu.crop)

    # 3. LLM/Final Answer
    if rag_source != "generic":
        # Direct RAG hit
        final_answer = format_knowledge_response(intent, entities, context_data)
        follow_ups = []
        source = "knowledge_base"
    else:
        # LLM Fallback (using history context)
        history_data = await get_chat_history(session_id)
        context_str = "\n".join([f"{h['role']}: {h['message']}" for h in history_data["history"][-4:]])
        
        final_answer, follow_ups = await call_llm(user_message, intent, entities, context_str)
        source = "llm"

    # 4. Save to history
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

@app.get("/api/chat/session")
async def sessions_endpoint():
    return await get_all_sessions()

@app.get("/api/chat/history/{session_id}")
async def history_endpoint(session_id: str):
    return await get_chat_history(session_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
