import psycopg
from pgvector.psycopg import register_vector

from app.config import DATABASE_URL, EMBED_DIM

SCHEMA_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    heading TEXT,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    access TEXT[] NOT NULL,
    restricted_override BOOLEAN NOT NULL DEFAULT FALSE,
    period TEXT,
    status TEXT,
    source TEXT,
    supersedes TEXT,
    superseded_by TEXT,
    embedding VECTOR({EMBED_DIM}) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_access_gin ON chunks USING GIN (access);
"""


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    # Must run before register_vector(): the "vector" type has to exist in
    # the database before psycopg can look up its OID to adapt for it.
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_SQL)