import os

import pytest

from app.pdf_extract import extract_text

SAMPLE_PDF = os.path.join(os.path.dirname(__file__), "..", "data", "sample.pdf")

pytestmark = pytest.mark.unit


def test_extract_text_returns_non_empty_known_content():
    text = extract_text(SAMPLE_PDF)
    assert text.strip() != ""
    assert "Helios Labs" in text  


def test_extract_text_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        extract_text("/no/such/file.pdf")