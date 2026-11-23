
from netsol.graphs.state import ChatGraphState
from netsol.services.llm import LLMService
from netsol.core.config import get_settings
from netsol.core.exceptions import LLMResponseValidationError
from netsol.graphs.prompts import build_conversation_prompt
def make_generate_response_node(llm_service: LLMService):

    async def generate_response(
        state: ChatGraphState,
    ) -> dict:

        prompt = build_conversation_prompt(
        context_messages=state["context_messages"],
        user_message=state["user_message"],
            )

        result = await llm_service.generate_reply(prompt)

        return {
            "answer": result.answer,
            "model": result.model,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        }

    return generate_response

def validate_response(state: ChatGraphState) -> dict:

    answer = state.get("answer")

    if not isinstance(answer, str):
        raise LLMResponseValidationError()

    answer = answer.strip()

    if not answer or not any(
        character.isprintable() and not character.isspace()
        for character in answer
    ):
        raise LLMResponseValidationError()

    settings = get_settings()

    if len(answer) > settings.llm_max_output_chars:
        raise LLMResponseValidationError()

    return {
        "answer": answer,
    }