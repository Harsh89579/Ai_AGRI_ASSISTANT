import sqlite3
import os

DB_PATH = "services/chat_orchestrator/data/agri_knowledge.db"

def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Fertilizer Table
    cur.execute("DROP TABLE IF EXISTS fertilizer")
    cur.execute("""
    CREATE TABLE fertilizer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        recommendation TEXT NOT NULL
    )
    """)
    fertilizers = [
        ("wheat", "Wheat needs 120-150 kg Nitrogen, 60 kg Phosphorus, and 40 kg Potassium per hectare."),
        ("rice", "Rice requires 100 kg Nitrogen, 50 kg Phosphorus, and 50 kg Potassium. Zinc sulfate is also recommended."),
        ("tomato", "Tomatoes benefit from 100-120 kg Nitrogen and high Potassium for fruit quality.")
    ]
    cur.executemany("INSERT INTO fertilizer (crop_name, recommendation) VALUES (?, ?)", fertilizers)

    # 2. Disease Table
    cur.execute("DROP TABLE IF EXISTS disease")
    cur.execute("""
    CREATE TABLE disease (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        disease_name TEXT NOT NULL,
        recommendation TEXT NOT NULL
    )
    """)
    diseases = [
        ("wheat", "Rust", "Use propiconazole or tebuconazole fungicides."),
        ("tomato", "Early Blight", "Yellow spots with concentric rings. Use Mancozeb or Copper Oxychloride."),
        ("rice", "Blast", "Maintain proper water levels and use Tricyclazole.")
    ]
    cur.executemany("INSERT INTO disease (crop_name, disease_name, recommendation) VALUES (?, ?, ?)", diseases)

    # 3. Crop Calendar
    cur.execute("DROP TABLE IF EXISTS crop_calendar")
    cur.execute("""
    CREATE TABLE crop_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        sowing_month TEXT NOT NULL,
        harvesting_month TEXT NOT NULL
    )
    """)
    calendar = [
        ("wheat", "November to December", "April to May"),
        ("rice", "June to July", "November to December"),
        ("tomato", "October to November", "February to March")
    ]
    cur.executemany("INSERT INTO crop_calendar (crop_name, sowing_month, harvesting_month) VALUES (?, ?, ?)", calendar)

    conn.commit()
    conn.close()
    print(f"✅ Database seeded at {DB_PATH}")

if __name__ == "__main__":
    seed()
