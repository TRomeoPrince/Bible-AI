import os
import httpx


class IQBibleClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("IQBIBLE_API_KEY")
        self.base_url = base_url or os.getenv("IQBIBLE_BASE_URL", "https://api.iqbible.com")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("IQBIBLE_API_KEY is not configured.")
        return {"Authorization": f"Bearer {self.api_key}"}

    async def get(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                self.base_url.rstrip("/") + "/" + path.lstrip("/"),
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
