import pytest
from pgvector import Vector

from app.db import get_connection, init_schema
from app.retrieval import get_document_chunks, search

pytestmark = pytest.mark.integration

FAKE_VECTOR = [0.1] * 1536


def _stub_embed(query: str) -> list[float]:
    return FAKE_VECTOR


@pytest.fixture
def seeded_conn():
    conn = get_connection()
    init_schema(conn)
    conn.execute("TRUNCATE TABLE chunks")
    rows = [
        ("doc-sales.pdf", "Sales Doc", None, 0, "Sales playbook content", ["sales"], Vector(FAKE_VECTOR)),
        ("doc-people.pdf", "People Doc", None, 0, "Compensation bands content", ["people"], Vector(FAKE_VECTOR)),
        ("doc-mixed.pdf", "Mixed Doc", None, 0, "Intro visible to everyone", ["sales", "people"], Vector(FAKE_VECTOR)),
        ("doc-mixed.pdf", "Mixed Doc", None, 1, "Restricted detail", ["people"], Vector(FAKE_VECTOR)),
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (doc_id, title, heading, chunk_index, content, access, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
    yield conn
    conn.execute("TRUNCATE TABLE chunks")
    conn.close()


def test_sales_role_never_receives_people_only_content(seeded_conn):
    results = search(["sales"], "anything", k=10, embed_fn=_stub_embed)
    contents = [r.content for r in results]
    assert "Compensation bands content" not in contents
    assert "Restricted detail" not in contents
    assert "Sales playbook content" in contents
    assert "Intro visible to everyone" in contents


def test_people_role_receives_people_only_content(seeded_conn):
    results = search(["people"], "anything", k=10, embed_fn=_stub_embed)
    contents = [r.content for r in results]
    assert "Compensation bands content" in contents
    assert "Restricted detail" in contents
    assert "Sales playbook content" not in contents


def test_role_with_no_matches_gets_empty_list(seeded_conn):
    results = search(["exec"], "anything", k=10, embed_fn=_stub_embed)
    assert results == []


def test_get_document_chunks_excludes_restricted_chunk_for_unauthorized_caller(seeded_conn):
    chunks = get_document_chunks(["sales"], "doc-mixed.pdf")
    contents = [c.content for c in chunks]
    assert "Intro visible to everyone" in contents
    assert "Restricted detail" not in contents


def test_get_document_chunks_includes_everything_for_authorized_caller(seeded_conn):
    chunks = get_document_chunks(["people"], "doc-mixed.pdf")
    contents = [c.content for c in chunks]
    assert "Intro visible to everyone" in contents
    assert "Restricted detail" in contents