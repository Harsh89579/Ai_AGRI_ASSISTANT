from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from fastapi.concurrency import run_in_threadpool
import sqlite3

app = FastAPI(title="AI Agri Assistant - RAG / Knowledge Service")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path("/app/data/agri_knowledge.db")

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

@app.get("/health")
async def health():
    return {"status": "ok", "service": "rag_service"}

# ---------------- DB HELPERS (SYNC) ----------------

def _get_fertilizer_recommendation(crop: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "SELECT recommendation FROM fertilizer WHERE LOWER(crop_name) = ?",
        (crop,),
    )
    row = cur.fetchone()
    conn.close()
    return row

def _get_disease_info(crop: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT disease_name, recommendation
        FROM disease
        WHERE LOWER(crop_name) = ?
        LIMIT 1
        """,
        (crop,),
    )
    row = cur.fetchone()
    conn.close()
    return row

def _get_crop_calendar(crop: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sowing_month, harvesting_month
        FROM crop_calendar
        WHERE LOWER(crop_name) = ?
        """,
        (crop,),
    )
    row = cur.fetchone()
    conn.close()
    return row

# ---------------- Query Endpoint ----------------

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(req: QueryRequest):

    intent = req.intent.lower()
    crop = (req.crop or "").lower()

    try:
        # 🌾 Fertilizer
        if intent == "fertilizer" and crop:
            row = await run_in_threadpool(_get_fertilizer_recommendation, crop)
            if row:
                return QueryResponse(
                    context=row[0],
                    source="fertilizer_table",
                )

        # 🦠 Disease
        if intent == "disease" and crop:
            row = await run_in_threadpool(_get_disease_info, crop)
            if row:
                disease_name, rec = row
                return QueryResponse(
                    context=f"{disease_name}: {rec}",
                    source="disease_table",
                )

        # 🌱 Crop calendar
        if intent == "general" and crop:
            row = await run_in_threadpool(_get_crop_calendar, crop)
            if row:
                sowing, harvesting = row
                return QueryResponse(
                    context=(
                        f"{crop.capitalize()} aam taur par "
                        f"{sowing} me boya jata hai aur "
                        f"{harvesting} me kaata jata hai."
                    ),
                    source="crop_calendar",
                )

    except Exception as e:
        print("❌ RAG ERROR:", e)

    return QueryResponse(
        context=(
            "Abhi is query ke liye specific data nahi mila. "
            "Future version me yahan se documents / PDFs se context aayega."
        ),
        source="generic",
    )