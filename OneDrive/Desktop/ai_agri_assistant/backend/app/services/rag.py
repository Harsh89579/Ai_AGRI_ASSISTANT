import aiosqlite
from pathlib import Path
from loguru import logger
from rapidfuzz import process, fuzz
from ..config import DB_PATH

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
    try:
        all_crops = await _get_all_crops()
        if not all_crops: return user_crop
        
        match = process.extractOne(user_crop, all_crops, scorer=fuzz.WRatio)
        if match and match[1] > 70:
            logger.info(f"Fuzzy match: {user_crop} -> {match[0]} (score: {match[1]})")
            return str(match[0])
    except Exception as e:
        logger.error(f"Fuzzy find error: {e}")
    return user_crop

async def query_knowledge(intent: str, crop: str | None, message: str):
    intent = intent.lower()
    raw_crop = (crop or "").lower()
    
    # 🧠 Fuzzy search for crop
    target_crop = await fuzzy_find_crop(raw_crop) or raw_crop

    try:
        # 🌾 Fertilizer
        if intent == "fertilizer" and target_crop:
            row = await _get_fertilizer_recommendation(target_crop)
            if row:
                logger.info(f"RAG hit (fertilizer): {target_crop}")
                return {"context": row[0], "source": "fertilizer_table"}

        # 🦠 Disease
        if intent == "disease" and target_crop:
            row = await _get_disease_info(target_crop)
            if row:
                disease_name, rec = row
                logger.info(f"RAG hit (disease): {target_crop}")
                return {"context": f"{disease_name}: {rec}", "source": "disease_table"}

        # 🌱 Crop calendar
        if intent == "general" and target_crop:
            row = await _get_crop_calendar(target_crop)
            if row:
                sowing, harvesting = row
                logger.info(f"RAG hit (calendar): {target_crop}")
                return {
                    "context": f"{target_crop.capitalize()} aam taur par {sowing} me boya jata hai aur {harvesting} me kaata jata hai.",
                    "source": "crop_calendar"
                }

    except Exception as e:
        logger.error(f"RAG Service Error: {e}")

    return {
        "context": "Abhi is query ke liye specific data nahi mila. Future version me yahan se documents / PDFs se context aayega.",
        "source": "generic"
    }
