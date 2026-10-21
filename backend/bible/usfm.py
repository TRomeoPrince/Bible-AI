import re

BOOK_TO_USFM = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM", "Deuteronomy": "DEU",
    "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "1 Samuel": "1SA", "2 Samuel": "2SA",
    "1 Kings": "1KI", "2 Kings": "2KI", "1 Chronicles": "1CH", "2 Chronicles": "2CH",
    "Ezra": "EZR", "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalms": "PSA",
    "Proverbs": "PRO", "Ecclesiastes": "ECC", "Song Of Solomon": "SNG", "Isaiah": "ISA",
    "Jeremiah": "JER", "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS",
    "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON", "Micah": "MIC",
    "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG", "Zechariah": "ZEC",
    "Malachi": "MAL", "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN",
    "Acts": "ACT", "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO",
    "Galatians": "GAL", "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL",
    "1 Thessalonians": "1TH", "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI",
    "Titus": "TIT", "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN", "Jude": "JUD",
    "Revelation": "REV",
}

ALIASES = {
    "psalm": "Psalms", "psalms": "Psalms", "ps": "Psalms",
    "song of songs": "Song Of Solomon", "song of solomon": "Song Of Solomon", "songs": "Song Of Solomon",
    "jn": "John", "jhn": "John", "rom": "Romans", "rev": "Revelation",
    "1 cor": "1 Corinthians", "2 cor": "2 Corinthians",
    "1 thess": "1 Thessalonians", "2 thess": "2 Thessalonians",
    "1 tim": "1 Timothy", "2 tim": "2 Timothy",
    "1 pet": "1 Peter", "2 pet": "2 Peter",
}

for _book in list(BOOK_TO_USFM):
    ALIASES.setdefault(_book.lower(), _book)


def canonical_book(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip()).lower()
    if cleaned in ALIASES:
        return ALIASES[cleaned]
    return " ".join(x.capitalize() for x in cleaned.split())


def to_usfm(book: str, chapter: int, start_verse: int | None = None, end_verse: int | None = None) -> str:
    canonical = canonical_book(book)
    code = BOOK_TO_USFM.get(canonical)
    if not code:
        raise ValueError(f"Unknown Bible book: {book}")
    ref = f"{code}.{chapter}"
    if start_verse is not None:
        ref += f".{start_verse}"
        if end_verse and end_verse != start_verse:
            ref += f"-{end_verse}"
    return ref
