import aiosqlite
import uuid
from datetime import datetime
from loguru import logger
from ..config import DB_PATH
from .nlu import detect_intent_and_crop
from .rag import query_knowledge
from .llm import call_llm

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
    
    return [dict(row) for row in rows]

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
    return [dict(row) for row in rows]

async def process_chat(message: str, session_id: str | None = None):
    session_id = session_id or str(uuid.uuid4())
    logger.info(f"Processing chat for session {session_id}: {message[:50]}...")

    # 1. NLU
    nlu_result = detect_intent_and_crop(message)
    intent = nlu_result.intent
    crop = nlu_result.crop

    # 2. Get history for context (optional but good for LLM)
    history_rows = await get_chat_history(session_id)
    history_context = "\n".join([f"{h['role']}: {h['message']}" for h in history_rows[-5:]])

    # 3. RAG
    rag_result = await query_knowledge(intent, crop, message)
    context_data = rag_result["context"]
    source = rag_result["source"]

    # 4. LLM logic
    if source != "generic":
        # RAG Hit: Format response or let LLM polish it if needed
        # For now, let's keep the RAG Hit response as is or use LLM for better Hinglish
        final_answer, follow_ups = await call_llm(message, intent, {"crop": crop}, context_data)
        # Re-verify source
        res_source = "knowledge_base"
    else:
        # RAG Miss: Use LLM with history context
        final_answer, follow_ups = await call_llm(message, intent, {"crop": crop}, history_context)
        res_source = "llm"

    # 5. Save history
    try:
        await save_to_chat_history(session_id, "user", message)
        await save_to_chat_history(session_id, "bot", final_answer)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")

    return {
        "session_id": session_id,
        "reply": final_answer,
        "intent": intent,
        "entities": {"crop": crop},
        "source": res_source,
        "follow_ups": follow_ups
    }
