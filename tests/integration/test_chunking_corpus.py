import json
import os
from pathlib import Path

import pytest

from app.chunking import chunk_document
from app.pdf_extract import extract_text

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = os.environ.get("DATA_DIR", str(_REPO_ROOT / "data"))
PDFS_DIR = os.path.join(DATA_DIR, "pdfs")
MANIFEST_PATH = os.path.join(PDFS_DIR, "manifest.json")

EXPECTED_FACTS = {
    "general/product-pricing.pdf": "99",
    "u_priya/compensation-bands-2025.pdf": "85,000",
    "u_sam/q2-pipeline-report.pdf": "410,000",
    "u_erin/board-deck-q2-financials.pdf": "22.5M",
}


@pytest.fixture(scope="module")
def all_chunks():
    with open(MANIFEST_PATH) as f:
        documents = json.load(f)["documents"]
    result = {}
    for doc in documents:
        text = extract_text(os.path.join(PDFS_DIR, doc["path"]))
        result[doc["path"]] = chunk_document(text, default_access=doc["access"])
    return result


def test_expected_facts_survive_chunking(all_chunks):
    for doc_path, expected_substring in EXPECTED_FACTS.items():
        chunks = all_chunks[doc_path]
        assert any(expected_substring in c.content for c in chunks), (
            f"expected '{expected_substring}' somewhere in {doc_path}'s chunks, "
            f"found none -- a table or figure was likely swallowed"
        )


def test_exactly_two_chunks_are_narrowed_and_only_in_all_hands(all_chunks):
    narrowed = {
        doc_path: [c for c in chunks if c.restricted_override]
        for doc_path, chunks in all_chunks.items()
    }
    total_narrowed = sum(len(cs) for cs in narrowed.values())
    assert total_narrowed == 2
    assert len(narrowed["general/all-hands-2025-q2.pdf"]) == 2


def test_no_other_document_has_narrowed_chunks(all_chunks):
    for doc_path, chunks in all_chunks.items():
        if doc_path == "general/all-hands-2025-q2.pdf":
            continue
        assert not any(c.restricted_override for c in chunks), (
            f"{doc_path} had a chunk narrowed unexpectedly -- likely a banner "
            f"false positive"
        )