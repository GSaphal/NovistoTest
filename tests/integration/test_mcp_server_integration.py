import os
import subprocess
import sys
import time

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pgvector import Vector

pytestmark = pytest.mark.integration

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TEST_PORT = 18765
SERVER_URL = f"http://127.0.0.1:{TEST_PORT}/mcp"


def _seed_one_chunk(database_url):
    from app.db import get_connection, init_schema

    os.environ["DATABASE_URL"] = database_url
    conn = get_connection()
    init_schema(conn)
    conn.execute("TRUNCATE TABLE chunks")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (doc_id, title, heading, chunk_index, content, access, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            ("doc-a.pdf", "Doc A", None, 0, "sales-only content", ["sales"], Vector([0.1] * 1536)),
        )
    conn.close()


@pytest.fixture(scope="module")
def running_server(database_url=os.environ.get("DATABASE_URL", "postgresql://rag:rag@localhost:55432/rag")):
    _seed_one_chunk(database_url)
    env = {
        **os.environ,
        "DATA_DIR": FIXTURES_DIR,
        "DATABASE_URL": database_url,
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": str(TEST_PORT),
    }
    proc = subprocess.Popen([sys.executable, "-m", "app.mcp_server"], env=env)
    try:
        for _ in range(50):
            time.sleep(0.2)
            if proc.poll() is not None:
                raise RuntimeError("mcp_server process exited early")
        yield
    finally:
        proc.terminate()
        proc.wait(timeout=5)


async def _call(token, tool_name, arguments):
    async with streamable_http_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, {"token": token, **arguments})


@pytest.mark.asyncio
async def test_valid_token_returns_authorized_result(running_server):
    result = await _call("tok_sales_demo", "get_document", {"doc_id": "doc-a.pdf"})
    assert result.isError is False
    assert result.structuredContent["chunks"][0]["content"] == "sales-only content"


@pytest.mark.asyncio
async def test_invalid_token_returns_tool_error(running_server):
    result = await _call("not_a_real_token", "search_knowledge", {"query": "content", "k": 5})
    assert result.isError is True