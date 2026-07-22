import json
import os

from pgvector import Vector

from app.chunking import chunk_document
from app.config import MANIFEST_PATH, PDFS_DIR
from app.db import get_connection, init_schema
from app.embeddings import embed_batch
from app.pdf_extract import extract_text


def load_manifest(manifest_path: str) -> list[dict]:
    with open(manifest_path) as f:
        return json.load(f)["documents"]


def run_ingestion(manifest_path: str, pdfs_dir: str, conn, embed_fn=embed_batch) -> int:
    documents = load_manifest(manifest_path)
    init_schema(conn)
    conn.execute("TRUNCATE TABLE chunks")

    total_chunks = 0
    for doc in documents:
        pdf_path = os.path.join(pdfs_dir, doc["path"])
        text = extract_text(pdf_path)
        chunks = chunk_document(text, default_access=doc["access"])
        if not chunks:
            continue

        vectors = embed_fn([c.content for c in chunks])
        rows = [
            (
                doc["path"], doc["title"], chunk.heading, i, chunk.content,
                chunk.access, chunk.restricted_override, doc.get("period"),
                doc.get("status"), doc.get("source"), doc.get("supersedes"),
                doc.get("superseded_by"), Vector(vector),
            )
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO chunks (
                    doc_id, title, heading, chunk_index, content, access,
                    restricted_override, period, status, source, supersedes,
                    superseded_by, embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        total_chunks += len(rows)

    return total_chunks


def main() -> None:
    conn = get_connection()
    total = run_ingestion(MANIFEST_PATH, PDFS_DIR, conn)
    print(f"Ingested {total} chunks.")


if __name__ == "__main__":
    main()