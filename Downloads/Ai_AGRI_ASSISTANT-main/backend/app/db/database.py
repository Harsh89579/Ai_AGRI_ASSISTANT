import os
import aiosqlite
from datetime import datetime
from pathlib import Path
from loguru import logger

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "app" / "db" / "agri_knowledge.db")))

# Ensure DB directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        # If adding new tables (fertilizer, disease, crop_calendar), 
        # normally they'd be here, but we'll assume they're already in the DB 
        # from the original microservices or seeded separately.
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
    return {"session_id": session_id, "history": [dict(row) for row in rows]}

async def get_all_sessions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT session_id, MIN(timestamp) as start_time FROM chat_history GROUP BY session_id ORDER BY MIN(timestamp) DESC"
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"session_id": row["session_id"], "start_time": row["start_time"]} for row in rows]
