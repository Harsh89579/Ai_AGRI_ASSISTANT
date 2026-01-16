import os, sys
from dotenv import load_dotenv

load_dotenv()

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")
PORT = int(os.getenv("PORT", 8000))

if not SERVICE_API_KEY:
    print("Missing SERVICE_API_KEY", file=sys.stderr)
    sys.exit(1)
