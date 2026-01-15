import asyncio
import httpx
from config import OPENAI_API_KEY, MODEL_NAME

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

async def call_llm_async(
    system: str,
    user: str,
    max_tokens: int = 350,
    timeout: int = 20,
    retries: int = 2,
) -> str:
    last_err = None

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries + 1):
            try:
                resp = await client.post(
                    OPENAI_URL,
                    headers=HEADERS,
                    json=payload,
                )
                resp.raise_for_status()

                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

            except Exception as e:
                last_err = e
                if attempt < retries:
                    await asyncio.sleep(1 + attempt)

    raise last_err