from dataclasses import dataclass

from pgvector import Vector

from app.db import get_connection
from app.embeddings import embed_one


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    heading: str | None
    chunk_index: int
    content: str
    score: float


def search(roles: list[str], query: str, k: int = 6, embed_fn=embed_one) -> list[RetrievedChunk]:
    if not roles:
        return []
    vector = Vector(embed_fn(query))
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT doc_id, title, heading, chunk_index, content,
                   1 - (embedding <=> %(vector)s) AS score
            FROM chunks
            WHERE access && %(roles)s
            ORDER BY embedding <=> %(vector)s
            LIMIT %(k)s
            """,
            {"vector": vector, "roles": roles, "k": k},
        )
        rows = cur.fetchall()
    return [
        RetrievedChunk(doc_id=r[0], title=r[1], heading=r[2], chunk_index=r[3], content=r[4], score=float(r[5]))
        for r in rows
    ]


def get_document_chunks(roles: list[str], doc_id: str) -> list[RetrievedChunk]:
    if not roles:
        return []
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT doc_id, title, heading, chunk_index, content
            FROM chunks
            WHERE doc_id = %(doc_id)s AND access && %(roles)s
            ORDER BY chunk_index
            """,
            {"doc_id": doc_id, "roles": roles},
        )
        rows = cur.fetchall()
    return [
        RetrievedChunk(doc_id=r[0], title=r[1], heading=r[2], chunk_index=r[3], content=r[4], score=1.0)
        for r in rows
    ]