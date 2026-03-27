import httpx
import json
from loguru import logger
from ..config import GROQ_API_KEY, GROQ_MODEL
from ..utils.formatter import build_prompt

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

async def call_llm(user_message: str, intent: str, entities: dict, context_data: str):
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set")
        return "Service temporarily unavailable (API Key missing).", []

    prompt = build_prompt(user_message, intent, entities, context_data)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ],
        "temperature": 0.4,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }
    
    # Check if model supports json_object (Llama 3 does)
    # If using a model that doesn't, we'd remove response_format
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GROQ_URL, headers=headers, json=payload)
            
            if resp.status_code != 200:
                logger.error(f"Groq API Error: {resp.status_code} {resp.text}")
                raise RuntimeError(f"Groq API Error: {resp.status_code}")

            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                parsed = json.loads(content)
                return parsed.get("answer", content), parsed.get("follow_ups", [])
            except json.JSONDecodeError:
                return content, []

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return (
            "Is sawal ke liye abhi exact jankari uplabdh nahi hai. "
            "Aam taur par, fasal ki behtar paidaawar ke liye mitti ki jaanch (soil test) karwana aur "
            "kisi nikatam krishi kendra (agricultural center) se sampark karna sabse achha kadam hota hai.",
            ["Mitti ki jaanch kaise karwayein?", "Najdiki krishi kendra kahan hai?"]
        )
