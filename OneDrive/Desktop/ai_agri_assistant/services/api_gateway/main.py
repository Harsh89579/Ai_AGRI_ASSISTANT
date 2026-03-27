from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Agri Assistant - API Gateway", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import uuid
from fastapi import Request

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

import os
import psutil
CHAT_ORCHESTRATOR_URL = os.getenv("CHAT_ORCHESTRATOR_URL", "http://chat_orchestrator:8000")

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    source: str = "unknown"
    follow_ups: list[str] = []

@app.get("/health", tags=["system"])
async def health_check():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "status": "ok", 
        "service": "api_gateway",
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
    }


@app.get("/api/chat/session")
async def proxy_chat_sessions(request: Request):
    try:
        headers = {"X-Trace-ID": request.state.trace_id}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            res = await client.get(f"{CHAT_ORCHESTRATOR_URL}/api/chat/session")
            res.raise_for_status()
            return res.json()
    except Exception as e:
        print(f"❌ Session proxy error: {e}")
        return []


@app.get("/api/chat/history/{session_id}")
async def proxy_chat_history(session_id: str, request: Request):
    try:
        headers = {"X-Trace-ID": request.state.trace_id}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            res = await client.get(
                f"{CHAT_ORCHESTRATOR_URL}/api/chat/history/{session_id}"
            )
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request):
    headers = {"X-Trace-ID": request.state.trace_id}
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        try:
            resp = await client.post(
                f"{CHAT_ORCHESTRATOR_URL}/chat",
                json=payload.dict(),
            )

            if resp.status_code != 200:
                print("❌ Orchestrator non-200:", resp.status_code, resp.text)
                raise httpx.HTTPStatusError(
                    "Non-200 from orchestrator",
                    request=resp.request,
                    response=resp
                )

            data = resp.json()
            return ChatResponse(**data)

        except Exception as e:
            print("❌ Gateway exception:", repr(e))
            return ChatResponse(
                session_id=payload.session_id or "unknown",
                reply=f"Backend error (chat orchestrator unavailable): {repr(e)}",
            )
