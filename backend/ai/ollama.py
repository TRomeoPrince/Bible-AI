import os

import httpx


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    async def available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(self.base_url + "/api/tags")
                return response.is_success
        except Exception:
            return False

    async def chat(self, messages: list[dict], temperature: float = 0.25) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self.base_url + "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("message", {}).get("content", "").strip()
