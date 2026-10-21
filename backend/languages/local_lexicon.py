import json
from pathlib import Path

from backend.languages.models import LexiconEntry
from backend.languages.providers import LexiconProvider


class LocalJsonLexiconProvider(LexiconProvider):
    """
    Generic loader for local lexicon JSON files.

    Supported shape:
    {
      "G25": {
        "lemma": "agapao",
        "transliteration": "agapao",
        "definitions": ["to love"],
        "source": "Thayer"
      }
    }
    """

    def __init__(self, files: list[Path]):
        self.files = files

    def lookup_strong(self, strong_number: str) -> list[LexiconEntry]:
        key = strong_number.upper().strip()
        results: list[LexiconEntry] = []

        for path in self.files:
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            item = payload.get(key)
            if not item:
                continue

            definitions = item.get("definitions") or []
            if isinstance(definitions, str):
                definitions = [definitions]

            results.append(
                LexiconEntry(
                    strong_number=key,
                    language="Greek" if key.startswith("G") else "Hebrew",
                    lemma=item.get("lemma"),
                    transliteration=item.get("transliteration"),
                    definitions=definitions,
                    source=item.get("source", path.stem),
                    source_license=item.get("source_license"),
                    source_url=item.get("source_url"),
                )
            )

        return results
