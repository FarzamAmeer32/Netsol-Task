
from netsol.graphs.state import ChatContextMessage


def build_conversation_prompt(
    context_messages: list[ChatContextMessage],
    user_message: str,
) -> str:

    prompt = (
        "You are a helpful assistant. "
        "Answer the user's message clearly and accurately.\n\n"
    )

    if context_messages:
        prompt += "Previous conversation:\n"

        for message in context_messages:
            role = message["role"].capitalize()

            prompt += f"{role}: {message['content']}\n"

        prompt += "\n"

    prompt += f"Current user message:\n{user_message}"

    return prompt
