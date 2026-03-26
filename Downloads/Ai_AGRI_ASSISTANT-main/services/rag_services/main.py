from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import aiosqlite
from loguru import logger
from rapidfuzz import process, fuzz

app = FastAPI(title="AI Agri Assistant - RAG / Knowledge Service")

import os
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", "/app/data/agri_knowledge.db"))

print("📌 RAG DB PATH:", DB_PATH)

# ---------------- Models ----------------

class QueryRequest(BaseModel):
    intent: str
    crop: str | None = None
    message: str

class QueryResponse(BaseModel):
    context: str
    source: str

# ---------------- Health ----------------

import uuid
from fastapi import Request
import psutil

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

@app.get("/health")
async def health():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "status": "ok", 
        "service": "rag_service",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }

# ---------------- DB HELPERS (ASYNC) ----------------

async def _get_all_crops() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT crop_name FROM fertilizer") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def _get_fertilizer_recommendation(crop: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT recommendation FROM fertilizer WHERE LOWER(crop_name) = ?",
            (crop,),
        ) as cursor:
            return await cursor.fetchone()

async def _get_disease_info(crop: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT disease_name, recommendation
            FROM disease
            WHERE LOWER(crop_name) = ?
            LIMIT 1
            """,
            (crop,),
        ) as cursor:
            return await cursor.fetchone()

async def _get_crop_calendar(crop: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT sowing_month, harvesting_month
            FROM crop_calendar
            WHERE LOWER(crop_name) = ?
            """,
            (crop,),
        ) as cursor:
            return await cursor.fetchone()

async def fuzzy_find_crop(user_crop: str) -> str | None:
    if not user_crop: return None
    all_crops = await _get_all_crops()
    if not all_crops: return user_crop
    
    match = process.extractOne(user_crop, all_crops, scorer=fuzz.WRatio)
    if match and match[1] > 70:
        logger.info(f"Fuzzy match: {user_crop} -> {match[0]} (score: {match[1]})")
        return str(match[0])
    return user_crop

# ---------------- Query Endpoint ----------------

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(req: QueryRequest):
    intent = req.intent.lower()
    raw_crop = (req.crop or "").lower()
    
    # 🧠 Fuzzy search for crop
    crop = await fuzzy_find_crop(raw_crop) or raw_crop

    try:
        # 🌾 Fertilizer
        if intent == "fertilizer" and crop:
            row = await _get_fertilizer_recommendation(crop)
            if row:
                logger.info(f"RAG hit (fertilizer): {crop}")
                return QueryResponse(
                    context=row[0],
                    source="fertilizer_table",
                )

        # 🦠 Disease
        if intent == "disease" and crop:
            row = await _get_disease_info(crop)
            if row:
                disease_name, rec = row
                logger.info(f"RAG hit (disease): {crop}")
                return QueryResponse(
                    context=f"{disease_name}: {rec}",
                    source="disease_table",
                )

        # 🌱 Crop calendar
        if intent == "general" and crop:
            row = await _get_crop_calendar(crop)
            if row:
                sowing, harvesting = row
                logger.info(f"RAG hit (calendar): {crop}")
                return QueryResponse(
                    context=(
                        f"{crop.capitalize()} aam taur par "
                        f"{sowing} me boya jata hai aur "
                        f"{harvesting} me kaata jata hai."
                    ),
                    source="crop_calendar",
                )

    except Exception as e:
        logger.error(f"RAG Service Error: {e}")

    return QueryResponse(
        context=(
            "Abhi is query ke liye specific data nahi mila. "
            "Future version me yahan se documents / PDFs se context aayega."
        ),
        source="generic",
    )