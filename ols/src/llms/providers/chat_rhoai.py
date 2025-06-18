"""Workaround for the compatibility issue between max_tokens and max_completion_tokens."""

from typing import Any, List, Optional

from langchain_core.language_models import LanguageModelInput
from langchain_openai import ChatOpenAI


class ChatRHOAI(ChatOpenAI):
    """Workaround for the compatibility issue between max_tokens and max_completion_tokens."""

    def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if "max_completion_tokens" in payload:
            payload["max_tokens"] = payload.pop("max_completion_tokens")
        return payload
