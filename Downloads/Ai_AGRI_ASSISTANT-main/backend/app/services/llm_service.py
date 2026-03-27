import os
import httpx
import json
from loguru import logger

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

async def call_llm(user_message: str, intent: str, entities: dict, context_data: str) -> tuple[str, list[str]]:
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set")
        return "I am having trouble accessing the AI service right now. Please try again later.", []

    system_prompt = (
        "You are an agriculture expert. Reply in simple Hinglish. "
        "Keep steps short and practical. End with ONE next action for farmer. "
        "If you are unsure, ask a concise clarifying question."
    )

    # Simple prompt builder
    user_prompt = (
        f"User Query: {user_message}\n"
        f"Intent: {intent}\n"
        f"Entities: {entities}\n"
        f"Context from Knowledge Base/History: {context_data}\n\n"
        "Please provide a simple and practical answer in Hinglish."
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 300
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if resp.status_code != 200:
                logger.error(f"Groq API error: {resp.status_code} {resp.text}")
                return "Maaf karein, AI engine abhi respond nahi kar raha hai.", []

            content = resp.json()["choices"][0]["message"]["content"].strip()
            
            # Simple heuristic for follow-ups (if LLM were to return them, but for now we fallback)
            follow_ups = []
            if "soil test" in content.lower():
                follow_ups.append("Mitti ki jaanch kaise karein?")
            
            return content, follow_ups

    except Exception as e:
        logger.error(f"LLM call exception: {e}")
        return "Technical error in LLM service.", []

def format_knowledge_response(intent: str, entities: dict, context_data: str) -> str:
    crop = entities.get("crop") if isinstance(entities, dict) else None
    if context_data:
        if crop:
            return f"{crop.capitalize()} ke liye jankari: {context_data}"
        return f"Jankari: {context_data}"
    
    # Fallback placeholders
    if intent == "fertilizer": return "Khaad ki sahi matra ke liye fasal ka naam batayein."
    if intent == "disease": return "Fasal ke lakshan batayein taki hum beemari pehchan sakein."
    return "Abhi is sawal ke liye mere paas database me jankari nahi hai."
