import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "agri_knowledge.db")

# Security
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "supersecret-service-key")

# Server
PORT = int(os.getenv("PORT", 8000))
