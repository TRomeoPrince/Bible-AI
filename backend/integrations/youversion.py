import os
from typing import Any

import httpx


BASE_URL = "https://api.youversion.com/v1"


class YouVersionClient:
    def __init__(self, app_key: str | None = None):
        self.app_key = app_key or os.getenv("YOUVERSION_APP_KEY")

    @property
    def configured(self) -> bool:
        return bool(self.app_key)

    def _headers(self) -> dict[str, str]:
        if not self.app_key:
            raise RuntimeError("YOUVERSION_APP_KEY is not configured.")
        return {
            "X-YVP-App-Key": self.app_key,
            "Accept": "application/json",
        }

    async def _get(self, path: str, params: Any = None) -> dict:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(
                BASE_URL + path,
                params=params,
                headers=self._headers(),
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                raise RuntimeError(f"YouVersion rate limit reached. Retry after {retry_after}s.")
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()

    async def get_bibles(
        self,
        language_ranges: list[str] | None = None,
        all_available: bool = False,
        page_size: int = 99,
        page_token: str | None = None,
    ) -> dict:
        ranges = language_ranges or ["en"]
        params: list[tuple[str, str | int | bool]] = [
            ("page_size", page_size),
        ]
        if all_available:
            params.append(("all_available", "true"))
        for language in ranges:
            params.append(("language_ranges[]", language))
        if page_token:
            params.append(("page_token", page_token))
        return await self._get("/bibles", params=params)

    async def get_all_bibles(
        self,
        language_ranges: list[str] | None = None,
        all_available: bool = False,
    ) -> list[dict]:
        data: list[dict] = []
        token: str | None = None
        while True:
            payload = await self.get_bibles(
                language_ranges=language_ranges,
                all_available=all_available,
                page_token=token,
            )
            data.extend(payload.get("data", []))
            token = payload.get("next_page_token")
            if not token:
                break
        return data

    async def get_bible(self, bible_id: int) -> dict:
        return await self._get(f"/bibles/{bible_id}")

    async def get_passage(
        self,
        bible_id: int,
        usfm_reference: str,
        format: str = "text",
    ) -> dict:
        return await self._get(
            f"/bibles/{bible_id}/passages/{usfm_reference}",
            params={"format": format},
        )

    async def find_bible(self, abbreviation: str, language: str = "en") -> dict | None:
        wanted = abbreviation.strip().upper()
        bibles = await self.get_all_bibles([language], all_available=False)
        for bible in bibles:
            candidates = {
                str(bible.get("abbreviation", "")).upper(),
                str(bible.get("localized_abbreviation", "")).upper(),
            }
            if wanted in candidates:
                return bible
        return None
