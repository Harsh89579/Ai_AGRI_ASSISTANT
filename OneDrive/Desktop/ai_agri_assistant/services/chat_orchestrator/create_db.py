import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "agri_knowledge.db"

print("\n📌 Creating / refreshing SQLite DB at:", DB_PATH, "\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS fertilizer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT NOT NULL,
    recommendation TEXT NOT NULL
)
""")


cur.execute("DELETE FROM fertilizer")

fert_rows = [
    (
        "gehu",
        "Gehu ke liye 120–130 kg Urea + 50–60 kg DAP per acre behtar hota hai. "
        "Sahi matra mitti ki report aur khet ke size par depend karti hai."
    ),
    (
        "dhaan",
        "Dhaan ke liye 40–50 kg DAP + 100–120 kg Urea ko 2–3 hisson me dena chahiye. "
        "Ek hissa ropai ke kuch din baad, baaki tillering ke dauran."
    ),
    (
        "sarson",
        "Sarson ke liye 40–50 kg DAP + 40–50 kg Urea per acre sahi mana jata hai. "
        "Potash ki jarurat mitti ke hisab se ho sakti hai."
    )
]

cur.executemany(
    "INSERT INTO fertilizer (crop_name, recommendation) VALUES (?, ?)",
    fert_rows
)

cur.execute("""
CREATE TABLE IF NOT EXISTS disease (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT NOT NULL,
    symptom_keywords TEXT NOT NULL,   -- comma separated keywords
    disease_name TEXT NOT NULL,
    recommendation TEXT NOT NULL
)
""")

cur.execute("DELETE FROM disease")

disease_rows = [
    (
        "gehu",
        "bhura,daag,patta",   
        "Brown Rust / Leaf Rust",
        "Gehu ke patton par chhote bhure daag ya pustule agar dikh rahe hain to ye Brown Rust ho sakta hai. "
        "Resistant variety ka istemal karein, santulit khaad den, aur zarurat par manayata-prapt fungicide "
        "jaise Propiconazole 0.1% ka prayog karein (label anusar)."
    ),
    (
        "gehu",
        "peela,daag,patta",
        "Yellow Rust",
        "Agar patton par peeli dhariyan / daag dikh rahe hain to ye Yellow Rust ho sakta hai. "
        "Surakshit fungicide spray (Propiconazole / Tebuconazole) label dose par karein aur "
        "infected khet ko observation me rakhein."
    ),
    (
        "dhaan",
        "neck,blast,daag,panicle",
        "Neck Blast",
        "Dhaan ke panicle ke neck hissa par kaale daag ya todna jaisa symptom Neck Blast ka sanket hai. "
        "Resistant variety, santulit nitrogen aur manayata-prapt fungicide jaise Tricyclazole ka prayog karein."
    ),
    (
        "dhaan",
        "brown,spot,daag,patta",
        "Brown Leaf Spot",
        "Dhaan ke patte par gol ya aniyamit bhure daag Brown Leaf Spot ho sakte hain. "
        "Balanced khaad, khadhe pani se bachein, aur zarurat par appropriate fungicide spray karein."
    ),
    (
        "sarson",
        "safed,daag,patta,white",
        "White Rust / Safed Sundi",
        "Sarson ke patton par ubhre safed chhale jaisa symptom White Rust ka ho sakta hai. "
        "Beej upchar, rog-rodhak variety aur manayata-prapt fungicide ka istemal karein."
    )
]

cur.executemany(
    "INSERT INTO disease (crop_name, symptom_keywords, disease_name, recommendation) "
    "VALUES (?, ?, ?, ?)",
    disease_rows
)

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS crop_calendar (
    crop_name TEXT PRIMARY KEY,
    sowing_month TEXT NOT NULL,
    harvesting_month TEXT NOT NULL
)
""")

cur.execute("DELETE FROM crop_calendar")
crop_calendar_rows = [
    ("gehu", "October–November", "March–April"),
    ("dhaan", "June–July", "October–November"),
    ("sarson", "October", "February–March")
]

cur.executemany(
    "INSERT INTO crop_calendar (crop_name, sowing_month, harvesting_month) VALUES (?, ?, ?)",
    crop_calendar_rows
)



conn.commit()
conn.close()

print("✅ DB Ready: Fertilizer + Disease + Crop Calendar data inserted successfully!\n")

