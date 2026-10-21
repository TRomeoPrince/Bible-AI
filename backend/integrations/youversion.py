import os
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
        return {"X-YVP-App-Key": self.app_key}

    async def get_bibles(self):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{BASE_URL}/bibles", headers=self._headers())
            response.raise_for_status()
            return response.json()
