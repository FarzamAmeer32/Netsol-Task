from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from netsol.graphs.nodes import (
    make_generate_response_node,
    validate_response,
)
from netsol.graphs.state import ChatGraphState
from netsol.services.llm import LLMService


def build_chat_graph(
    llm_service: LLMService,
    checkpointer: BaseCheckpointSaver,
):
    builder = StateGraph(ChatGraphState)

    builder.add_node(
        "generate_response",
        make_generate_response_node(llm_service),
    )

    builder.add_node("validate_response", validate_response)

    builder.add_edge(START, "generate_response")
    builder.add_edge("generate_response", "validate_response")
    builder.add_edge("validate_response", END)

    return builder.compile(checkpointer=checkpointer)