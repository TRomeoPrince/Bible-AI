from pydantic import BaseModel, Field


class WordStudyEntry(BaseModel):
    language: str
    surface: str | None = None
    lemma: str | None = None
    transliteration: str | None = None
    pronunciation: str | None = None
    strong_number: str | None = None
    morphology: str | None = None
    gloss: str | None = None
    source: str
    source_license: str | None = None
    source_url: str | None = None


class LexiconEntry(BaseModel):
    strong_number: str
    language: str
    lemma: str | None = None
    transliteration: str | None = None
    definitions: list[str] = Field(default_factory=list)
    source: str
    source_license: str | None = None
    source_url: str | None = None
