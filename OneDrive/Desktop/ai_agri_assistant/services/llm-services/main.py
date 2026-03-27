from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
import time
import json
import time
from fastapi.concurrency import run_in_threadpool

from config import SERVICE_API_KEY
from services.llm_client import call_llm
from utils.formatter import build_prompt

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ---------------- App Init ----------------

app = FastAPI(title="AI Agri Assistant - LLM Service")

import uuid
from fastapi import Request
import os
import psutil

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

@app.get("/health")
async def health():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "status": "ok", 
        "service": "llm_service",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }

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
        # Expecting a JSON string back from the LLM
        raw_answer = await run_in_threadpool(
            call_llm,
            prompt["system"],
            prompt["user"]
        )
        
        try:
            parsed_response = json.loads(raw_answer)
            answer = parsed_response.get("answer", "Maaf karein, main theek se samajh nahi paaya.")
            follow_ups = parsed_response.get("follow_ups", [])
        except json.JSONDecodeError:
            # Fallback if LLM didn't return valid JSON
            answer = raw_answer
            follow_ups = []

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
                "Aam taur par, fasal ki behtar paidaawar ke liye mitti ki jaanch (soil test) karwana aur "
                "kisi nikatam krishi kendra (agricultural center) se sampark karna sabse achha kadam hota hai. "
                "Aap apni fasal ya zameen ke baare me kuch aur detail batana chahenge?"
            ),
            "follow_ups": ["Mitti ki jaanch kaise karwayein?", "Najdiki krishi kendra kahan hai?"],
            "metadata": {
                "error": str(e),
                "circuit_open": CIRCUIT_OPEN
            }
        }

    latency = time.time() - start_time
    REQ_LATENCY.observe(latency)

    return {
        "final_answer": answer,
        "follow_ups": follow_ups,
        "metadata": {
            "model": "groq",
            "latency_s": latency
        }
    }

# ---------------- Metrics Endpoint ----------------

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)