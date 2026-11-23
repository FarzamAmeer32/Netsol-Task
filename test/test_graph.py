
import asyncio

import pytest
from langgraph.checkpoint.memory import MemorySaver

from netsol.core.config import get_settings
from netsol.core.exceptions import (
    LLMResponseValidationError,
    LLMUnavailableError,
)
from netsol.graphs.builder import build_chat_graph
from netsol.graphs.nodes import (
    make_generate_response_node,
    validate_response,
)
from netsol.services.llm import LLMResult


class FakeLLMService:

    def __init__(self, answer="Test answer", error=None):
        self.answer = answer
        self.error = error
        self.received_message = None

    async def generate_reply(self, message: str) -> LLMResult:
        self.received_message = message

        if self.error:
            raise self.error

        return LLMResult(
            answer=self.answer,
            model="fake-model",
            input_tokens=5,
            output_tokens=10,
        )


def test_generate_response_node():
    fake_llm = FakeLLMService()

    node = make_generate_response_node(fake_llm)

    result = asyncio.run(
        node({
            "context_messages": [],
            "user_message": "Hello",
        })
    )

    assert result["answer"] == "Test answer"
    assert result["model"] == "fake-model"
    assert result["input_tokens"] == 5
    assert result["output_tokens"] == 10

    assert "Hello" in fake_llm.received_message


def test_validate_response_strips_whitespace():
    result = validate_response({
        "user_message": "Hello",
        "answer": "  Test answer  ",
    })

    assert result["answer"] == "Test answer"


@pytest.mark.parametrize(
    "answer",
    [None, "", "   ", "\n\t", "\x00"],
)
def test_validate_response_rejects_invalid_answers(answer):
    with pytest.raises(LLMResponseValidationError):
        validate_response({
            "user_message": "Hello",
            "answer": answer,
        })


def test_validate_response_rejects_oversized_answer():
    max_chars = get_settings().llm_max_output_chars

    with pytest.raises(LLMResponseValidationError):
        validate_response({
            "user_message": "Hello",
            "answer": "A" * (max_chars + 1),
        })


def test_complete_graph_execution():
    fake_llm = FakeLLMService(
        answer="  Hello from LangGraph!  "
    )

    graph = build_chat_graph(
        fake_llm,
        MemorySaver(),
    )

    result = asyncio.run(
        graph.ainvoke(
            {
                "context_messages": [],
                "user_message": "Hello",
            },
            config={
                "configurable": {
                    "thread_id": "test-thread",
                }
            },
        )
    )

    assert result["answer"] == "Hello from LangGraph!"
    assert result["model"] == "fake-model"
    assert result["input_tokens"] == 5
    assert result["output_tokens"] == 10


def test_graph_propagates_llm_errors():
    fake_llm = FakeLLMService(
        error=LLMUnavailableError()
    )

    graph = build_chat_graph(
        fake_llm,
        MemorySaver(),
    )

    with pytest.raises(LLMUnavailableError):
        asyncio.run(
            graph.ainvoke(
                {
                    "context_messages": [],
                    "user_message": "Hello",
                },
                config={
                    "configurable": {
                        "thread_id": "test-thread",
                    }
                },
            )
        )
