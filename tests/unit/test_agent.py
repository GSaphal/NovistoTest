import json
from types import SimpleNamespace

import pytest

import app.agent as agent_module

pytestmark = pytest.mark.unit


class _FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = SimpleNamespace(name=name, arguments=json.dumps(arguments))


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content}


class _FakeSession:
    def __init__(self, result=None):
        self.calls = []
        self._result = result or SimpleNamespace(isError=False, structuredContent={"ok": True})

    async def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        return self._result


def test_tool_schema_strips_token_parameter():
    fake_tool = SimpleNamespace(
        name="search_knowledge",
        description="search",
        inputSchema={
            "type": "object",
            "properties": {"token": {"type": "string"}, "query": {"type": "string"}},
            "required": ["token", "query"],
        },
    )
    spec = agent_module._mcp_tool_to_openai_spec(fake_tool)
    params = spec["function"]["parameters"]
    assert "token" not in params["properties"]
    assert "token" not in params["required"]
    assert "query" in params["properties"]


@pytest.mark.asyncio
async def test_model_supplied_token_is_always_overridden():
    session = _FakeSession()
    tool_call = _FakeToolCall(
        call_id="call_1",
        name="search_knowledge",
        arguments={"token": "tok_exec_demo", "query": "acquisition"},  # model tries another user's token
    )

    await agent_module._execute_tool_call(session, tool_call, real_token="tok_sales_demo")

    tool_name, sent_args = session.calls[0]
    assert tool_name == "search_knowledge"
    assert sent_args["token"] == "tok_sales_demo"  # real caller identity always wins


@pytest.mark.asyncio
async def test_conversation_loop_stops_after_max_rounds(monkeypatch):
    session = _FakeSession()
    always_calls_a_tool = _FakeMessage(
        content=None,
        tool_calls=[_FakeToolCall("call_x", "search_knowledge", {"query": "anything"})],
    )
    monkeypatch.setattr(agent_module, "_next_model_response", lambda messages, tools: always_calls_a_tool)

    result = await agent_module._run_conversation(session, openai_tools=[], messages=[], token="tok_sales_demo")

    assert "allotted tool-call budget" in result["answer"]
    assert len(session.calls) == agent_module.MAX_TOOL_ROUNDS