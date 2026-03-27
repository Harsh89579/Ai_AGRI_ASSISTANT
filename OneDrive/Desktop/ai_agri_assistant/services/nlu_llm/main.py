from fastapi import FastAPI
from pydantic import BaseModel
from nlu import detect_intent_and_crop, NLUResult

app = FastAPI(title="AI Agri Assistant - NLU/LLM Service")


class AnalyzeRequest(BaseModel):
    message: str


class AnalyzeResponse(BaseModel):
    intent: str
    crop: str | None = None
    language: str

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
        "service": "nlu_llm",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    Abhi ke liye: sirf rule-based NLU.
    Future me: yahin se LLM + RAG bhi call kara sakte hain.
    """
    nlu: NLUResult = detect_intent_and_crop(req.message)

    return AnalyzeResponse(
     intent=nlu.intent,
     crop=nlu.crop,
     language=nlu.language
    )
