from pathlib import Path

from backend.bible.models import AccessMode, TranslationInfo, TranslationPermissions
from backend.bible.providers.local_json import LocalJsonBibleProvider


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "data" / "translations"
PRIVATE_DIR = ROOT / "data" / "private_translations"


CATALOG = {
    "WEB": TranslationInfo(
        code="WEB",
        name="World English Bible",
        provider="local_json",
        access_mode=AccessMode.LOCAL_PUBLIC,
        permissions=TranslationPermissions(
            local_storage_allowed=True,
            ai_grounding_allowed=True,
            caching_allowed=True,
            redistribution_allowed=True,
            notes="Public-domain/open distribution source intended for local installation.",
        ),
        available=False,
    ),
    "KJV": TranslationInfo(
        code="KJV",
        name="King James Version",
        provider="local_json",
        access_mode=AccessMode.LOCAL_PUBLIC,
        permissions=TranslationPermissions(
            local_storage_allowed=True,
            ai_grounding_allowed=True,
            caching_allowed=True,
            redistribution_allowed=True,
            notes="Use a verified public-domain edition and retain source metadata.",
        ),
        available=False,
    ),
    "ASV": TranslationInfo(
        code="ASV",
        name="American Standard Version",
        provider="local_json",
        access_mode=AccessMode.LOCAL_PUBLIC,
        permissions=TranslationPermissions(
            local_storage_allowed=True,
            ai_grounding_allowed=True,
            caching_allowed=True,
            redistribution_allowed=True,
        ),
        available=False,
    ),
    "BSB": TranslationInfo(
        code="BSB",
        name="Berean Standard Bible",
        provider="local_json",
        access_mode=AccessMode.LOCAL_PUBLIC,
        permissions=TranslationPermissions(
            local_storage_allowed=True,
            ai_grounding_allowed=True,
            caching_allowed=True,
            redistribution_allowed=True,
            notes="Install only from a source whose current license permits the intended use.",
        ),
        available=False,
    ),
    "ESV": TranslationInfo(
        code="ESV",
        name="English Standard Version",
        provider="esv_api",
        access_mode=AccessMode.OFFICIAL_API,
        permissions=TranslationPermissions(
            local_storage_allowed=False,
            ai_grounding_allowed=False,
            caching_allowed=False,
            redistribution_allowed=False,
            notes="Official API integration is planned; permissions must be respected at request time.",
        ),
        available=False,
    ),
    "NIV": TranslationInfo(
        code="NIV",
        name="New International Version",
        provider="licensed",
        access_mode=AccessMode.UNAVAILABLE,
        permissions=TranslationPermissions(
            notes="AI use requires an express license from the rights holder.",
        ),
        available=False,
    ),
}


local_provider = LocalJsonBibleProvider([PUBLIC_DIR, PRIVATE_DIR])


def list_translations() -> list[TranslationInfo]:
    installed = {item.code: item for item in local_provider.translations()}
    result: list[TranslationInfo] = []
    for code, item in CATALOG.items():
        result.append(installed.get(code, item))
    for code, item in installed.items():
        if code not in CATALOG:
            result.append(item)
    return sorted(result, key=lambda item: item.code)
