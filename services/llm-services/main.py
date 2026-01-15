from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time
from services.llm_client import call_llm_async
from config import SERVICE_API_KEY
from utils.formatter import build_prompt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ---------------- App Init ----------------

app = FastAPI(title="AI Agri Assistant - LLM Service")

REQ_COUNT = Counter("llm_requests_total", "Total LLM requests")
REQ_LATENCY = Histogram("llm_request_latency_seconds", "LLM request latency")

# ---------------- Circuit Breaker State ----------------

CIRCUIT_OPEN = False
CIRCUIT_UNTIL = 0
FAIL_COUNT = 0

FAIL_THRESHOLD = 3      # consecutive failures
COOLDOWN = 30           # seconds

# ---------------- Weak Response Detection ----------------

WEAK_PHRASES = [
    "sorry",
    "as an ai",
    "i am not sure",
    "cannot help",
    "no information",
    "please provide"
]

def is_weak_response(text: str) -> bool:
    if not text:
        return True
    if len(text.strip()) < 40:
        return True
    t = text.lower()
    return any(p in t for p in WEAK_PHRASES)

# ---------------- Request Model ----------------

class LLMRequest(BaseModel):
    user_message: str
    intent: str
    entities: dict = {}
    context_data: str = ""
    request_id: str | None = None

# ---------------- LLM Generate Endpoint ----------------

@app.post("/generate")
async def generate(req: LLMRequest, x_api_key: str = Header(None)):

    # ✅ global declaration MUST be at top
    global FAIL_COUNT, CIRCUIT_OPEN, CIRCUIT_UNTIL

    # 🔐 Auth check
    if x_api_key != SERVICE_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🔌 Circuit breaker check
    now = time.time()
    if CIRCUIT_OPEN and now < CIRCUIT_UNTIL:
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable, please try again shortly"
        )

    REQ_COUNT.inc()
    start_time = time.time()

    prompt = build_prompt(
        req.user_message,
        req.intent,
        req.entities,
        req.context_data
    )

    try:
        answer = await call_llm_async(
            prompt["system"],
            prompt["user"]
        )


        # STEP-2C
        if is_weak_response(answer):
            raise ValueError("Weak LLM response detected")

        # ✅ success → reset breaker
        FAIL_COUNT = 0
        CIRCUIT_OPEN = False

    except Exception as e:
        FAIL_COUNT += 1
        if FAIL_COUNT >= FAIL_THRESHOLD:
            CIRCUIT_OPEN = True
            CIRCUIT_UNTIL = time.time() + COOLDOWN

        REQ_LATENCY.observe(time.time() - start_time)

        return {
            "final_answer": (
                "Abhi AI response reliable nahi hai.\n"
                "👉 Kripya crop ka naam, "
                "uski stage (jaise 20–25 din), "
                "aur problem ke lakshan batayein.\n"
                "Main turant madad karunga."
            ),
            "metadata": {
                "error": str(e),
                "circuit_open": CIRCUIT_OPEN
            }
        }

    latency = time.time() - start_time
    REQ_LATENCY.observe(latency)

    return {
        "final_answer": answer,
        "metadata": {
            "model": "llm-service",
            "latency_s": latency
        }
    }

# ---------------- Metrics Endpoint ----------------

@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}