"""Similarity check by LLM."""

import logging
from time import sleep

from langchain_core.prompts.prompt import PromptTemplate

from .constants import MAX_RETRY_ATTEMPTS, TIME_TO_BREATH
from .prompts import ANSWER_SIMILARITY_PROMPT

logger = logging.getLogger(__name__)


class AnswerSimilarityScore:
    """Get similarity score generated by LLM."""

    def __init__(self, judge_llm):
        """Initialize."""
        prompt = PromptTemplate.from_template(ANSWER_SIMILARITY_PROMPT)
        self._judge_llm = prompt | judge_llm

    def get_score(
        self,
        question,
        answer,
        response,
        retry_attemps=MAX_RETRY_ATTEMPTS,
        time_to_breath=TIME_TO_BREATH,
    ):
        """Generate similarity score."""
        for _ in range(retry_attemps):
            try:
                result = self._judge_llm.invoke(
                    {
                        "question": question,
                        "answer": answer,
                        "response": response,
                    }
                )
                score = float(result.content) / 10
                break
            except Exception:
                # Continue with score as None
                score = None

            sleep(time_to_breath)

        return score
