
from typing import Literal, NotRequired, TypedDict


class ChatContextMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class ChatGraphState(TypedDict):
    context_messages: list[ChatContextMessage]
    user_message: str

    answer: NotRequired[str]
    model: NotRequired[str]
    input_tokens: NotRequired[int | None]
    output_tokens: NotRequired[int | None]
