from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time
from fastapi.concurrency import run_in_threadpool

from config import SERVICE_API_KEY
from services.llm_client import call_llm
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
        # ✅ Sync LLM safely called inside async endpoint
        answer = await run_in_threadpool(
            call_llm,
            prompt["system"],
            prompt["user"]
        )

        # success → reset breaker
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
                "Is sawal ke liye abhi exact jankari uplabdh nahi hai. "
                "Kripya thoda aur detail batayein."
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
            "model": "groq",
            "latency_s": latency
        }
    }

# ---------------- Metrics Endpoint ----------------

@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}