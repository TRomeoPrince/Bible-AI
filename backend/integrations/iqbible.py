import os
from typing import Any

import httpx


class IQBibleClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("IQBIBLE_API_KEY")
        self.base_url = (base_url or os.getenv("IQBIBLE_BASE_URL", "https://api.iqbible.com")).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("IQBIBLE_API_KEY is not configured.")
        return {
            "X-IQBible-API-Key": self.api_key,
            "Accept": "application/json",
        }

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(
                self.base_url + "/" + path.lstrip("/"),
                params=params,
                headers=self._headers(),
            )
            if response.status_code in (429, 503):
                retry_after = response.headers.get("Retry-After", "unknown")
                raise RuntimeError(f"IQ Bible temporarily unavailable/rate-limited. Retry after {retry_after}s.")
            response.raise_for_status()
            return response.json()

    async def licensing(self) -> Any:
        return await self.get("/api/v2/licensing")

    async def credits(self) -> Any:
        return await self.get("/api/v2/credits")

    async def ai_context(self, ref: str, **params) -> Any:
        query = {"ref": ref}
        query.update(params)
        return await self.get("/api/v2/ai/context", params=query)

    async def strongs(self, strong_number: str) -> Any:
        strong = strong_number.upper().strip()
        if not strong or strong[0] not in ("G", "H"):
            raise ValueError("Strong's number must start with G or H.")
        language = "greek" if strong.startswith("G") else "hebrew"
        return await self.get(f"/api/v2/lexicon/{language}/strongs/{strong}")

    async def morphology(self, code: str) -> Any:
        return await self.get(f"/api/v2/morphology/{code}")

    async def bible_catalog(self, **params) -> Any:
        return await self.get("/api/v2/bibles", params=params or None)

    async def bible_passage(self, version: str, book: str, chapter: int, verse: int | None = None) -> Any:
        path = f"/api/v2/bibles/{version}/{book}/{chapter}"
        if verse is not None:
            path += f"/{verse}"
        return await self.get(path)
