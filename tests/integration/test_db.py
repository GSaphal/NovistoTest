import pytest
from pgvector import Vector

from app.db import get_connection, init_schema

pytestmark = pytest.mark.integration


@pytest.fixture
def conn():
    c = get_connection()
    init_schema(c)
    c.execute("TRUNCATE TABLE chunks")
    yield c
    c.execute("TRUNCATE TABLE chunks")
    c.close()


def test_init_schema_is_idempotent(conn):
    init_schema(conn)  # second call must not raise
    init_schema(conn)


def test_vector_round_trip(conn):
    fake_embedding = [0.1] * 1536
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (doc_id, title, chunk_index, content, access, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            ("doc.pdf", "Doc", 0, "hello world", ["marketing"], Vector(fake_embedding)),
        )
        cur.execute("SELECT content, access, embedding FROM chunks WHERE doc_id = %s", ("doc.pdf",))
        row = cur.fetchone()

    returned_embedding = row[2].to_list()  # pgvector returns a Vector, not a plain list

    assert row[0] == "hello world"
    assert row[1] == ["marketing"]
    assert len(returned_embedding) == 1536
    assert abs(returned_embedding[0] - 0.1) < 1e-6