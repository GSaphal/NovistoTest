import os

import pytest
from fastapi.testclient import TestClient

import app.api as api_module

pytestmark = pytest.mark.unit

FIXTURE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(autouse=True)
def fixture_users(monkeypatch):
    monkeypatch.setenv("DATA_DIR", FIXTURE_DATA_DIR)
    import app.identity as identity_module

    identity_module.get_users_by_token.cache_clear()


@pytest.fixture
def client():
    return TestClient(api_module.app)


def test_missing_authorization_header_returns_401(client):
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 401


def test_malformed_authorization_header_returns_401(client):
    response = client.post("/ask", json={"question": "hello"}, headers={"Authorization": "tok_sales_demo"})
    assert response.status_code == 401


def test_invalid_token_returns_401_and_never_calls_the_agent(client, monkeypatch):
    called = False

    async def fail_if_called(token, question):
        nonlocal called
        called = True
        return {"answer": "should not happen"}

    monkeypatch.setattr(api_module, "answer_question", fail_if_called)

    response = client.post(
        "/ask", json={"question": "hello"}, headers={"Authorization": "Bearer not_a_real_token"}
    )

    assert response.status_code == 401
    assert called is False  # the fast-fail actually short-circuited


def test_valid_token_returns_200_with_agent_answer(client, monkeypatch):
    async def fake_answer(token, question):
        assert token == "tok_sales_demo"
        return {"answer": f"answer to: {question}"}

    monkeypatch.setattr(api_module, "answer_question", fake_answer)

    response = client.post(
        "/ask", json={"question": "hello"}, headers={"Authorization": "Bearer tok_sales_demo"}
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "answer to: hello"}