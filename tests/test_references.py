from backend.bible.references import extract_reference, parse_reference
from backend.bible.usfm import to_usfm


def test_john_reference():
    ref = parse_reference("John 3:3")
    assert ref.book == "John"
    assert ref.chapter == 3
    assert ref.start_verse == 3
    assert ref.canonical() == "John 3:3"


def test_alias_and_range():
    ref = parse_reference("Jn 3:3-5")
    assert ref.book == "John"
    assert ref.canonical() == "John 3:3-5"


def test_natural_language_reference():
    ref = extract_reference("Please explain Romans 8:28-30 in context.")
    assert ref is not None
    assert ref.canonical() == "Romans 8:28-30"


def test_usfm_conversion():
    ref = parse_reference("1 Corinthians 13:4-7")
    assert to_usfm(ref.book, ref.chapter, ref.start_verse, ref.end_verse) == "1CO.13.4-7"
