import re
from dataclasses import dataclass


BOOK_ALIASES = {
    "jn": "John",
    "john": "John",
    "rom": "Romans",
    "romans": "Romans",
    "ps": "Psalms",
    "psalm": "Psalms",
    "psalms": "Psalms",
    "1 cor": "1 Corinthians",
    "1 corinthians": "1 Corinthians",
    "gen": "Genesis",
    "genesis": "Genesis",
}


@dataclass(frozen=True)
class ParsedReference:
    book: str
    chapter: int
    start_verse: int | None = None
    end_verse: int | None = None

    def canonical(self) -> str:
        if self.start_verse is None:
            return f"{self.book} {self.chapter}"
        if self.end_verse and self.end_verse != self.start_verse:
            return f"{self.book} {self.chapter}:{self.start_verse}-{self.end_verse}"
        return f"{self.book} {self.chapter}:{self.start_verse}"


_REFERENCE_RE = re.compile(
    r"^\s*(?P<book>(?:[1-3]\s*)?[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+"
    r"(?P<chapter>\d+)"
    r"(?:\s*:\s*(?P<start>\d+)(?:\s*[-–]\s*(?P<end>\d+))?)?\s*$",
    re.IGNORECASE,
)


def parse_reference(value: str) -> ParsedReference:
    cleaned = value.strip()
    match = _REFERENCE_RE.match(cleaned)
    if not match:
        raise ValueError(f"Could not parse Bible reference: {value!r}")

    raw_book = re.sub(r"\s+", " ", match.group("book").strip()).lower()
    book = BOOK_ALIASES.get(raw_book)
    if not book:
        book = " ".join(part.capitalize() for part in raw_book.split())

    chapter = int(match.group("chapter"))
    start = int(match.group("start")) if match.group("start") else None
    end = int(match.group("end")) if match.group("end") else start

    return ParsedReference(book=book, chapter=chapter, start_verse=start, end_verse=end)
