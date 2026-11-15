
from typing import NotRequired, TypedDict


class ChatGraphState(TypedDict):
    user_message: str
    answer: NotRequired[str]
    model: NotRequired[str]
    input_tokens: NotRequired[int | None]
    output_tokens: NotRequired[int | None]

