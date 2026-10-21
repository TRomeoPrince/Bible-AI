import re
from dataclasses import dataclass


BOOK_ALIASES = {
    "gen": "Genesis", "genesis": "Genesis",
    "ex": "Exodus", "exo": "Exodus", "exodus": "Exodus",
    "lev": "Leviticus", "leviticus": "Leviticus",
    "num": "Numbers", "numbers": "Numbers",
    "deut": "Deuteronomy", "deuteronomy": "Deuteronomy",
    "josh": "Joshua", "joshua": "Joshua",
    "judg": "Judges", "judges": "Judges",
    "ruth": "Ruth",
    "1 sam": "1 Samuel", "1 samuel": "1 Samuel",
    "2 sam": "2 Samuel", "2 samuel": "2 Samuel",
    "1 kings": "1 Kings", "2 kings": "2 Kings",
    "1 chr": "1 Chronicles", "1 chronicles": "1 Chronicles",
    "2 chr": "2 Chronicles", "2 chronicles": "2 Chronicles",
    "ezra": "Ezra", "neh": "Nehemiah", "nehemiah": "Nehemiah",
    "est": "Esther", "esther": "Esther", "job": "Job",
    "ps": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "prov": "Proverbs", "proverbs": "Proverbs",
    "eccl": "Ecclesiastes", "ecclesiastes": "Ecclesiastes",
    "song of solomon": "Song Of Solomon", "song of songs": "Song Of Solomon",
    "isa": "Isaiah", "isaiah": "Isaiah", "jer": "Jeremiah", "jeremiah": "Jeremiah",
    "lam": "Lamentations", "lamentations": "Lamentations",
    "ezek": "Ezekiel", "ezekiel": "Ezekiel", "dan": "Daniel", "daniel": "Daniel",
    "hos": "Hosea", "hosea": "Hosea", "joel": "Joel", "amos": "Amos",
    "obad": "Obadiah", "obadiah": "Obadiah", "jonah": "Jonah", "mic": "Micah", "micah": "Micah",
    "nah": "Nahum", "nahum": "Nahum", "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "zeph": "Zephaniah", "zephaniah": "Zephaniah", "hag": "Haggai", "haggai": "Haggai",
    "zech": "Zechariah", "zechariah": "Zechariah", "mal": "Malachi", "malachi": "Malachi",
    "matt": "Matthew", "matthew": "Matthew", "mark": "Mark", "mk": "Mark",
    "luke": "Luke", "lk": "Luke", "jn": "John", "john": "John",
    "acts": "Acts", "rom": "Romans", "romans": "Romans",
    "1 cor": "1 Corinthians", "1 corinthians": "1 Corinthians",
    "2 cor": "2 Corinthians", "2 corinthians": "2 Corinthians",
    "gal": "Galatians", "galatians": "Galatians", "eph": "Ephesians", "ephesians": "Ephesians",
    "phil": "Philippians", "philippians": "Philippians",
    "col": "Colossians", "colossians": "Colossians",
    "1 thess": "1 Thessalonians", "1 thessalonians": "1 Thessalonians",
    "2 thess": "2 Thessalonians", "2 thessalonians": "2 Thessalonians",
    "1 tim": "1 Timothy", "1 timothy": "1 Timothy",
    "2 tim": "2 Timothy", "2 timothy": "2 Timothy",
    "titus": "Titus", "philem": "Philemon", "philemon": "Philemon",
    "heb": "Hebrews", "hebrews": "Hebrews", "jas": "James", "james": "James",
    "1 pet": "1 Peter", "1 peter": "1 Peter", "2 pet": "2 Peter", "2 peter": "2 Peter",
    "1 john": "1 John", "2 john": "2 John", "3 john": "3 John",
    "jude": "Jude", "rev": "Revelation", "revelation": "Revelation",
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
    r"^\s*(?P<book>(?:[1-3]\s*)?[A-Za-z]+(?:\s+[A-Za-z]+){0,2})\s+"
    r"(?P<chapter>\d+)"
    r"(?:\s*:\s*(?P<start>\d+)(?:\s*[-–]\s*(?P<end>\d+))?)?\s*$",
    re.IGNORECASE,
)


def _canonical_book(raw: str) -> str:
    key = re.sub(r"\s+", " ", raw.strip()).lower()
    return BOOK_ALIASES.get(key, " ".join(part.capitalize() for part in key.split()))


def parse_reference(value: str) -> ParsedReference:
    cleaned = value.strip()
    match = _REFERENCE_RE.match(cleaned)
    if not match:
        raise ValueError(f"Could not parse Bible reference: {value!r}")

    book = _canonical_book(match.group("book"))
    chapter = int(match.group("chapter"))
    start = int(match.group("start")) if match.group("start") else None
    end = int(match.group("end")) if match.group("end") else start
    return ParsedReference(book=book, chapter=chapter, start_verse=start, end_verse=end)


def extract_reference(text: str) -> ParsedReference | None:
    """
    Finds references embedded in natural language, e.g.
    'What is written in John 3:3?' or 'Explain Romans 8:28-30.'
    """
    aliases = sorted(BOOK_ALIASES.keys(), key=len, reverse=True)
    book_pattern = "|".join(re.escape(x) for x in aliases)
    pattern = re.compile(
        rf"\b(?P<book>{book_pattern})\s+(?P<chapter>\d+)"
        rf"(?:\s*:\s*(?P<start>\d+)(?:\s*[-–]\s*(?P<end>\d+))?)?",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None
    book = _canonical_book(match.group("book"))
    chapter = int(match.group("chapter"))
    start = int(match.group("start")) if match.group("start") else None
    end = int(match.group("end")) if match.group("end") else start
    return ParsedReference(book, chapter, start, end)
