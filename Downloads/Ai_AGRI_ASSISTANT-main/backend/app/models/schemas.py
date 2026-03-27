from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    entities: Dict[str, Any]
    source: str
    follow_ups: List[str] = []

class NLUResult(BaseModel):
    intent: str
    crop: Optional[str] = None
    language: str = "hi-en"

class SessionResponse(BaseModel):
    session_id: str
    start_time: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, Any]]
