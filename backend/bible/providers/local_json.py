import json
from pathlib import Path

from backend.bible.models import AccessMode, PassageResult, TranslationInfo, TranslationPermissions, Verse
from backend.bible.providers.base import BibleProvider
from backend.bible.references import parse_reference


class LocalJsonBibleProvider(BibleProvider):
    """
    Reads translation files shaped as:
    {
      "translation": {...metadata...},
      "verses": {
        "John": {"3": {"3": "verse text"}}
      }
    }

    Public-domain/open translations may live in data/translations.
    User-supplied copyrighted files should live in data/private_translations,
    which is gitignored.
    """

    def __init__(self, directories: list[Path]):
        self.directories = directories
        self._files: dict[str, Path] = {}
        self._translations: dict[str, TranslationInfo] = {}
        self.reload()

    def reload(self) -> None:
        self._files.clear()
        self._translations.clear()

        for directory in self.directories:
            directory.mkdir(parents=True, exist_ok=True)
            for path in directory.glob("*.json"):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    meta = payload["translation"]
                    permissions = TranslationPermissions(**meta.get("permissions", {}))
                    info = TranslationInfo(
                        code=meta["code"].upper(),
                        name=meta["name"],
                        provider="local_json",
                        access_mode=AccessMode(meta.get("access_mode", "local_public")),
                        permissions=permissions,
                        attribution=meta.get("attribution"),
                        source_url=meta.get("source_url"),
                        available=True,
                    )
                    self._files[info.code] = path
                    self._translations[info.code] = info
                except Exception:
                    continue

    def translations(self) -> list[TranslationInfo]:
        return sorted(self._translations.values(), key=lambda item: item.code)

    def get_passage(self, translation: str, reference: str) -> PassageResult:
        code = translation.upper()
        if code not in self._files:
            raise KeyError(f"Translation {code} is not installed.")

        parsed = parse_reference(reference)
        payload = json.loads(self._files[code].read_text(encoding="utf-8"))
        chapter = payload["verses"].get(parsed.book, {}).get(str(parsed.chapter), {})
        if not chapter:
            raise KeyError(f"{parsed.book} {parsed.chapter} is not available in {code}.")

        if parsed.start_verse is None:
            verse_numbers = sorted((int(v) for v in chapter), key=int)
        else:
            end = parsed.end_verse or parsed.start_verse
            verse_numbers = list(range(parsed.start_verse, end + 1))

        verses = []
        for number in verse_numbers:
            text = chapter.get(str(number))
            if text is None:
                raise KeyError(f"{parsed.book} {parsed.chapter}:{number} is not available in {code}.")
            verses.append(Verse(book=parsed.book, chapter=parsed.chapter, verse=number, text=text))

        return PassageResult(
            reference=parsed.canonical(),
            translation=self._translations[code],
            verses=verses,
        )
