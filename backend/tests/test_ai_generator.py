"""Unit tests for AIGenerator (Anthropic client is mocked)."""
from unittest.mock import MagicMock, patch, call
import pytest

from ai_generator import AIGenerator


# ---------------------------------------------------------------------------
# Helpers to build mock Anthropic response objects
# ---------------------------------------------------------------------------

def _make_direct_response(text="This is a direct answer."):
    """Simulate a response with stop_reason=end_turn (no tool use)."""
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [content_block]
    return response


def _make_tool_use_response(tool_name="search_course_content", tool_input=None, tool_id="toolu_01"):
    """Simulate a response with stop_reason=tool_use."""
    if tool_input is None:
        tool_input = {"query": "Python basics"}

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_id

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]
    return response


def _make_generator():
    """Return an AIGenerator with a mocked Anthropic client."""
    gen = AIGenerator.__new__(AIGenerator)
    gen.model = "claude-test"
    gen.base_params = {"model": "claude-test", "temperature": 0, "max_tokens": 800}
    gen.client = MagicMock()
    return gen


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDirectResponse:
    def test_direct_response_no_tool_use(self):
        gen = _make_generator()
        direct = _make_direct_response("Hello world")
        gen.client.messages.create.return_value = direct

        result = gen.generate_response(query="What is 2+2?")

        assert result == "Hello world"
        assert gen.client.messages.create.call_count == 1

    def test_conversation_history_in_system_prompt(self):
        gen = _make_generator()
        gen.client.messages.create.return_value = _make_direct_response()

        gen.generate_response(query="Follow-up", conversation_history="User: Hi\nAssistant: Hello")

        call_kwargs = gen.client.messages.create.call_args[1]
        assert "Previous conversation" in call_kwargs["system"]
        assert "User: Hi" in call_kwargs["system"]


class TestToolUse:
    def test_tool_use_triggers_tool_execution(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response(tool_name="search_course_content",
                                            tool_input={"query": "basics"})
        final_resp = _make_direct_response("Here are the results.")
        gen.client.messages.create.side_effect = [tool_resp, final_resp]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "search result text"

        gen.generate_response(query="What is Python?", tool_manager=tool_manager,
                              tools=[{"name": "search_course_content"}])

        tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="basics"
        )

    def test_tool_result_sent_in_second_call(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response(tool_id="toolu_abc", tool_input={"query": "x"})
        final_resp = _make_direct_response("Final answer")
        gen.client.messages.create.side_effect = [tool_resp, final_resp]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "tool output"

        gen.generate_response(query="Q", tool_manager=tool_manager, tools=[{}])

        second_call_kwargs = gen.client.messages.create.call_args_list[1][1]
        messages = second_call_kwargs["messages"]
        tool_result_msg = messages[-1]
        assert tool_result_msg["role"] == "user"
        assert tool_result_msg["content"][0]["type"] == "tool_result"
        assert tool_result_msg["content"][0]["tool_use_id"] == "toolu_abc"
        assert tool_result_msg["content"][0]["content"] == "tool output"

    def test_final_response_returned_after_tool_use(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response()
        final_resp = _make_direct_response("Final text")
        gen.client.messages.create.side_effect = [tool_resp, final_resp]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "result"

        result = gen.generate_response(query="Q", tool_manager=tool_manager, tools=[{}])
        assert result == "Final text"

    def test_second_call_omits_tools(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response()
        final_resp = _make_direct_response()
        gen.client.messages.create.side_effect = [tool_resp, final_resp]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "result"

        gen.generate_response(query="Q", tool_manager=tool_manager,
                              tools=[{"name": "search_course_content"}])

        second_call_kwargs = gen.client.messages.create.call_args_list[1][1]
        assert "tools" not in second_call_kwargs

    def test_assistant_content_appended_to_messages(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response()
        final_resp = _make_direct_response()
        gen.client.messages.create.side_effect = [tool_resp, final_resp]

        tool_manager = MagicMock()
        tool_manager.execute_tool.return_value = "res"

        gen.generate_response(query="Q", tool_manager=tool_manager, tools=[{}])

        second_call_kwargs = gen.client.messages.create.call_args_list[1][1]
        messages = second_call_kwargs["messages"]
        # messages[0] = user, messages[1] = assistant tool call, messages[2] = tool result
        assistant_msg = messages[1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["content"] == tool_resp.content

    def test_no_tool_execution_without_tool_manager(self):
        gen = _make_generator()
        tool_resp = _make_tool_use_response()
        gen.client.messages.create.return_value = tool_resp

        # No tool_manager → falls through to response.content[0].text
        # The tool_block is a MagicMock with .text attribute auto-created
        result = gen.generate_response(query="Q", tools=[{}])
        # Should return content[0].text without raising
        assert result == tool_resp.content[0].text
