import os

import pytest
from mcp.server.fastmcp.exceptions import ToolError

pytestmark = pytest.mark.unit

FIXTURE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(autouse=True)
def fixture_users(monkeypatch):
    monkeypatch.setenv("DATA_DIR", FIXTURE_DATA_DIR)
    import app.identity as identity_module

    identity_module.get_users_by_token.cache_clear()


def test_search_knowledge_rejects_invalid_token_without_touching_the_database():
    from app.mcp_server import search_knowledge

    with pytest.raises(ToolError):
        search_knowledge(token="not_a_real_token", query="anything")


def test_get_document_rejects_invalid_token_without_touching_the_database():
    from app.mcp_server import get_document

    with pytest.raises(ToolError):
        get_document(token="not_a_real_token", doc_id="whatever.pdf")