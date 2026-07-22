import os

import pytest

from app.db import get_connection
from app.ingest import run_ingestion

pytestmark = pytest.mark.integration

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
MANIFEST_PATH = os.path.join(FIXTURES_DIR, "manifest.json")


def _stub_embed(texts: list[str]) -> list[list[float]]:
    # Fixed-size fake vectors
    return [[0.01 * i] * 1536 for i in range(len(texts))]


@pytest.fixture
def conn():
    c = get_connection()
    yield c
    c.execute("TRUNCATE TABLE chunks")
    c.close()


def test_ingestion_populates_expected_row_count(conn):
    total = run_ingestion(MANIFEST_PATH, FIXTURES_DIR, conn, embed_fn=_stub_embed)
    assert total > 0

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM chunks")
        assert cur.fetchone()[0] == total


def test_chunk_access_matches_manifest_per_document(conn):
    run_ingestion(MANIFEST_PATH, FIXTURES_DIR, conn, embed_fn=_stub_embed)

    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT access FROM chunks WHERE doc_id = %s", ("doc-a.pdf",))
        assert cur.fetchall() == [(["marketing"],)]

        cur.execute("SELECT DISTINCT access FROM chunks WHERE doc_id = %s", ("doc-b.pdf",))
        assert cur.fetchall() == [(["people"],)]


def test_running_ingestion_twice_does_not_double_rows(conn):
    first_total = run_ingestion(MANIFEST_PATH, FIXTURES_DIR, conn, embed_fn=_stub_embed)
    second_total = run_ingestion(MANIFEST_PATH, FIXTURES_DIR, conn, embed_fn=_stub_embed)
    assert first_total == second_total

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM chunks")
        assert cur.fetchone()[0] == second_total