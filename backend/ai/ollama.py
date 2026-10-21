import os

import httpx


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    async def tags(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(self.base_url + "/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])

    async def available(self) -> bool:
        try:
            await self.tags()
            return True
        except Exception:
            return False

    async def model_available(self) -> bool:
        try:
            wanted = self.model.lower()
            for model in await self.tags():
                name = str(model.get("name") or model.get("model") or "").lower()
                if name == wanted or name.startswith(wanted + ":"):
                    return True
            return False
        except Exception:
            return False

    async def chat(self, messages: list[dict], temperature: float = 0.25) -> str:
        if not await self.available():
            raise RuntimeError("Ollama is not running.")

        if not await self.model_available():
            raise RuntimeError(
                f"Ollama is running, but model '{self.model}' is not installed. "
                f"Run: ollama pull {self.model}"
            )

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
            if not response.is_success:
                detail = response.text[:500]
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {detail}")
            payload = response.json()
            return payload.get("message", {}).get("content", "").strip()
