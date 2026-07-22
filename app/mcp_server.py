from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from app import retrieval
from app.config import MCP_HOST, MCP_PORT
from app.identity import AuthError, get_users_by_token, resolve_token

mcp = FastMCP("knowledge-assistant", host=MCP_HOST, port=MCP_PORT, stateless_http=True)


def _roles_for(token: str) -> list[str]:
    try:
        user = resolve_token(token, get_users_by_token())
    except AuthError as e:
        raise ToolError(str(e)) from e
    return list(user.roles)


@mcp.tool()
def search_knowledge(token: str, query: str, k: int = 6) -> list[dict]:
    """Semantic search over the internal knowledge base, scoped to the
    caller's roles."""
    roles = _roles_for(token)
    results = retrieval.search(roles, query, k=k)
    return [
        {
            "doc_id": r.doc_id,
            "title": r.title,
            "heading": r.heading,
            "chunk_index": r.chunk_index,
            "content": r.content,
            "relevance": round(r.score, 4),
        }
        for r in results
    ]


@mcp.tool()
def get_document(token: str, doc_id: str) -> dict[str, Any]:
    """Fetch all chunks of a document the caller is entitled to see."""
    roles = _roles_for(token)
    chunks = retrieval.get_document_chunks(roles, doc_id)
    if not chunks:
        raise ToolError("No accessible content found for that document id.")
    return {
        "doc_id": doc_id,
        "title": chunks[0].title,
        "chunks": [
            {"chunk_index": c.chunk_index, "heading": c.heading, "content": c.content}
            for c in chunks
        ],
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
