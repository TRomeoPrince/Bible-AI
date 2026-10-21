from backend.bible.references import parse_reference


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
