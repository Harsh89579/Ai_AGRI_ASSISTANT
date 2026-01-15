import os, sys
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")
PORT = int(os.getenv("PORT", 7005))
if not OPENAI_API_KEY or not SERVICE_API_KEY:
    print("Error: Missing required environment variables.", file=sys.stderr);
    sys.exit(1)