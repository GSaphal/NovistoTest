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


def test_banner_narrows_access_when_stricter_than_document():
    text = (
        "Recognition\n"
        "Shout-out to the Support team for a record quarter.\n"
        "CONFIDENTIAL -- EXECUTIVE COMMITTEE ONLY. Do not distribute.\n"
        "We have signed a letter of intent to acquire a competitor.\n"
        "Recording and slides are in the All-Hands space.\n"
    )
    chunks = chunk_document(text, default_access=["marketing", "sales", "exec"])
    banner_chunk = next(c for c in chunks if "EXECUTIVE COMMITTEE" in c.content)
    following_chunk = chunks[chunks.index(banner_chunk) + 1]
    trailing_chunk = chunks[-1]

    assert banner_chunk.access == ["exec"]
    assert banner_chunk.restricted_override is True
    assert following_chunk.access == ["exec"]
    assert trailing_chunk.access == ["marketing", "sales", "exec"] 
    assert trailing_chunk.restricted_override is False


def test_banner_matching_documents_own_access_does_not_narrow():
    text = "CONFIDENTIAL -- People team only. Salary bands follow below."
    chunks = chunk_document(text, default_access=["people"])
    assert chunks[0].access == ["people"]
    assert chunks[0].restricted_override is False


def test_banner_naming_multiple_roles_keeps_all_of_them():
    text = "CONFIDENTIAL -- Executive & Finance only. Figures follow below."
    chunks = chunk_document(text, default_access=["exec", "finance"])
    assert chunks[0].access == ["exec", "finance"]
    assert chunks[0].restricted_override is False  


def test_chunk_with_no_banner_is_untouched():
    text = "Just a normal paragraph with nothing sensitive in it at all."
    chunks = chunk_document(text, default_access=["marketing"])
    assert chunks[0].access == ["marketing"]
    assert chunks[0].restricted_override is False