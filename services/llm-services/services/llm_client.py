import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_llm(system, user, max_tokens=300):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set inside container")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens
    }

    resp = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=20
    )

    # 🔥 VERY IMPORTANT FOR DEBUG
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.status_code} {resp.text}")

    return resp.json()["choices"][0]["message"]["content"].strip()
