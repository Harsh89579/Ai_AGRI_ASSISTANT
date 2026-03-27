import os
import aiosqlite
from loguru import logger
from rapidfuzz import process, fuzz
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "app" / "db" / "agri_knowledge.db")))

async def query_knowledge(intent: str, crop: str | None) -> tuple[str, str]:
    if not crop:
        return "", "generic"
    
    # 🧠 Fuzzy search or database retrieve
    crop = await _fuzzy_find_crop(crop.lower()) or crop.lower()

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if intent == "fertilizer":
                async with db.execute(
                    "SELECT recommendation FROM fertilizer WHERE LOWER(crop_name) = ?",
                    (crop,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row: return row[0], "fertilizer_table"

            elif intent == "disease":
                async with db.execute(
                    "SELECT disease_name, recommendation FROM disease WHERE LOWER(crop_name) = ? LIMIT 1",
                    (crop,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row: return f"{row[0]}: {row[1]}", "disease_table"

            elif intent == "general":
                async with db.execute(
                    "SELECT sowing_month, harvesting_month FROM crop_calendar WHERE LOWER(crop_name) = ?",
                    (crop,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row: 
                        return (
                            f"{crop.capitalize()} aam taur par {row[0]} me boya jata hai aur "
                            f"{row[1]} me kaata jata hai."
                        ), "crop_calendar"

    except Exception as e:
        logger.error(f"RAG query error: {e}")
    
    return "", "generic"

async def _fuzzy_find_crop(user_crop: str) -> str | None:
    if not user_crop: return None
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT DISTINCT crop_name FROM fertilizer") as cursor:
                rows = await cursor.fetchall()
                all_crops = [row[0] for row in rows]
        
        if not all_crops: return user_crop
        
        match = process.extractOne(user_crop, all_crops, scorer=fuzz.WRatio)
        if match and match[1] > 70:
            return str(match[0])
    except:
        pass
    return user_crop
