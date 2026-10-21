from enum import Enum
from pydantic import BaseModel, Field


class AccessMode(str, Enum):
    LOCAL_PUBLIC = "local_public"
    OFFICIAL_API = "official_api"
    USER_SUPPLIED_PRIVATE = "user_supplied_private"
    UNAVAILABLE = "unavailable"


class TranslationPermissions(BaseModel):
    local_storage_allowed: bool = False
    ai_grounding_allowed: bool = False
    caching_allowed: bool = False
    redistribution_allowed: bool = False
    notes: str | None = None


class TranslationInfo(BaseModel):
    code: str
    name: str
    provider: str
    access_mode: AccessMode
    permissions: TranslationPermissions
    attribution: str | None = None
    source_url: str | None = None
    available: bool = True


class Verse(BaseModel):
    book: str
    chapter: int = Field(ge=1)
    verse: int = Field(ge=1)
    text: str


class PassageResult(BaseModel):
    reference: str
    translation: TranslationInfo
    verses: list[Verse]
