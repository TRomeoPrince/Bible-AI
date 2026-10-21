import json
from pathlib import Path


class ThayerLexicon:
    def __init__(self, path: Path):
        self.path = path

    @property
    def installed(self) -> bool:
        return self.path.exists()

    def lookup(self, strong_number: str) -> list[dict]:
        strong = strong_number.upper().strip()
        if not self.installed or not strong.startswith("G"):
            return []

        results = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                linked = [str(x).upper() for x in item.get("strongs", [])]
                if strong in linked or str(item.get("id", "")).upper() == strong:
                    results.append({
                        "strong_number": strong,
                        "lemma": item.get("lemma"),
                        "lemma_normalized": item.get("lemma_normalized"),
                        "grammar": item.get("grammar"),
                        "definition": item.get("text"),
                        "paragraphs": item.get("paragraphs") or [],
                        "source": "Thayer's Greek-English Lexicon (1889)",
                        "license": "Public Domain / digitized dataset CC0 1.0",
                    })
        return results
