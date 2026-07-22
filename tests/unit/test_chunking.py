import pytest

from app.chunking import chunk_document

pytestmark = pytest.mark.unit


def test_heading_and_paragraph_are_split_correctly():
    text = "Highlights\nThis is a short paragraph about progress this quarter."
    chunks = chunk_document(text, default_access=["marketing"])
    assert len(chunks) == 1
    assert chunks[0].heading == "Highlights"
    assert "progress this quarter" in chunks[0].content


def test_wrapped_paragraph_lines_merge_into_one_chunk():
    text = (
        "As discussed under NDA at the exec offsite: we have signed a letter of intent\n"
        "to acquire Meridian Analytics for approximately $40M,\n"
        "expected to close in Q4."
    )
    chunks = chunk_document(text, default_access=["exec"])
    assert len(chunks) == 1
    assert "Meridian Analytics" in chunks[0].content
    assert "Q4." in chunks[0].content


def test_bullets_each_become_their_own_chunk():
    text = (
        "Highlights\n"
        "•  Crossed 1,000 paying customers.\n"
        "•  Lisbon office is now fully onboarded.\n"
    )
    chunks = chunk_document(text, default_access=["marketing"])
    assert len(chunks) == 2
    assert all(c.heading == "Highlights" for c in chunks)


def test_numeric_table_row_is_not_lost_as_a_heading():
    text = (
        "Engineering bands (annual base, CAD)\n"
        "Level Title Min Midpoint Max\n"
        "E2 Software Engineer 85,000 100,000 115,000\n"
    )
    chunks = chunk_document(text, default_access=["people"])
    assert any("85,000" in c.content for c in chunks)