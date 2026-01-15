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

@app.get("/health")
async def health():
    return {"status": "ok", "service": "nlu_llm"}


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
