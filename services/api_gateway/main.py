from fastapi import FastAPI, Depends
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException as HTTTPException

app = FastAPI(title="AI Agri Assistant - API Gateway", docs_url="/docs", openapi_url="/openapi.json")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHAT_ORCHESTRATOR_URL = "http://chat_orchestrator:8000"

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "api_gateway"}


@app.get("/api/chat/history/{session_id}")
async def proxy_chat_history(session_id: str):
    try:
        async with httpx.AsyncClient() as client:
         
         res = await client.get(
           f"http://chat_orchestrator:8000/api/chat/history/{session_id}"
       )

         res.raise_for_status()
         return res.json()
    except httpx.HTTPStatusError as e:
        raise HTTTPException(status_code=res.status_code, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    async with httpx.AsyncClient(timeout=60.0) as client:
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
