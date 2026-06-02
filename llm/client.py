import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_CHAIN = [
    os.getenv("LLM_PRIMARY", "google/gemini-flash-1.5"),
    os.getenv("LLM_FALLBACK_1", "groq/llama-3.1-70b-versatile"),
    os.getenv("LLM_FALLBACK_2", "groq/llama-3.1-8b-instant"),
]


async def complete(system: str, user: str, max_tokens: int = 600) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://parley.ai",
        "X-Title": "Parley Negotiation Copilot",
    }
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        for model in MODEL_CHAIN:
            try:
                payload["model"] = model
                r = await client.post(BASE_URL, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[llm] {model} failed: {e} — trying next")

    return '{"error": "All LLM providers exhausted"}'
