import re
from dataclasses import dataclass
from typing import Any

from backend.bible.references import parse_reference
from backend.bible.registry import local_provider
from backend.bible.usfm import to_usfm
from backend.integrations.youversion import YouVersionClient


@dataclass
class ScriptureSource:
    provider: str
    code: str
    name: str
    attribution: str | None
    bible_id: int | None = None


class ScriptureService:
    def __init__(self):
        self.youversion = YouVersionClient()

    async def list_translations(self, language: str = "en", include_unlicensed: bool = False) -> list[dict]:
        items: list[dict] = []
        for local in local_provider.translations():
            items.append({
                "code": local.code,
                "name": local.name,
                "provider": "local",
                "available": True,
                "attribution": local.attribution,
            })

        if self.youversion.configured:
            try:
                licensed_ids = {
                    int(b.get("id")) for b in await self.youversion.get_all_bibles([language], all_available=False)
                    if b.get("id") is not None
                }
                catalog = await self.youversion.get_all_bibles([language], all_available=include_unlicensed)
                for bible in catalog:
                    code = bible.get("localized_abbreviation") or bible.get("abbreviation") or str(bible.get("id"))
                    name = bible.get("localized_title") or bible.get("title") or bible.get("name") or code
                    bible_id = bible.get("id")
                    licensed = int(bible_id) in licensed_ids if bible_id is not None else False
                    items.append({
                        "code": code,
                        "name": name,
                        "provider": "youversion",
                        "available": licensed,
                        "licensed": licensed,
                        "bible_id": bible_id,
                        "copyright": bible.get("copyright"),
                        "attribution": bible.get("copyright") or bible.get("info"),
                    })
            except Exception:
                pass

        seen = set()
        result = []
        for item in items:
            key = (item.get("provider"), str(item.get("code")).upper(), item.get("bible_id"))
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    async def get_passage(
        self,
        reference: str,
        translation: str = "WEB",
        bible_id: int | None = None,
    ) -> dict:
        parsed = parse_reference(reference)

        if bible_id is None:
            try:
                local = local_provider.get_passage(translation, reference)
                return {
                    "reference": local.reference,
                    "provider": "local",
                    "translation": local.translation.model_dump(),
                    "verses": [v.model_dump() for v in local.verses],
                    "text": " ".join(v.text for v in local.verses),
                }
            except (KeyError, ValueError):
                pass

        if not self.youversion.configured:
            raise KeyError(f"{translation} is not installed locally and YouVersion is not configured.")

        bible = None
        if bible_id is not None:
            payload = await self.youversion.get_bible(bible_id)
            bible = payload.get("data", payload)
        else:
            bible = await self.youversion.find_bible(translation)

        if not bible:
            raise KeyError(f"Translation {translation} is not licensed/available through this YouVersion key.")

        resolved_id = int(bible.get("id") or bible_id)
        usfm = to_usfm(parsed.book, parsed.chapter, parsed.start_verse, parsed.end_verse)
        payload = await self.youversion.get_passage(resolved_id, usfm, format="text")
        data: Any = payload.get("data", payload)
        if isinstance(data, list):
            data = data[0] if data else {}

        text = str(data.get("content") or data.get("text") or "").strip()
        text = re.sub(r"\s+", " ", text)
        code = bible.get("localized_abbreviation") or bible.get("abbreviation") or translation
        name = bible.get("localized_title") or bible.get("title") or bible.get("name") or code
        attribution = bible.get("copyright") or bible.get("info") or data.get("copyright")

        return {
            "reference": parsed.canonical(),
            "provider": "youversion",
            "translation": {
                "code": code,
                "name": name,
                "provider": "youversion",
                "bible_id": resolved_id,
                "attribution": attribution,
            },
            "verses": [],
            "text": text,
            "raw": data,
        }

    async def compare(self, reference: str, translations: list[str]) -> list[dict]:
        results = []
        for code in translations:
            try:
                result = await self.get_passage(reference, code)
                results.append({"translation": code, "status": "ok", "result": result})
            except Exception as exc:
                results.append({"translation": code, "status": "unavailable", "error": str(exc)})
        return results
