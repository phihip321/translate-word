"""Skeleton OpenAI/GPT; không import SDK và không gọi API trong giai đoạn 3B."""

from app_v2.domain.models import TextChunk, TranslatedChunk
from .base import AITranslator, ProviderNotAvailableError


class OpenAITranslator(AITranslator):
    provider = "openai"

    def __init__(self, model: str) -> None:
        self.model = model

    def translate(self, chunk: TextChunk) -> TranslatedChunk:
        raise ProviderNotAvailableError("OpenAITranslator is a skeleton; API calls are disabled in phase 3B.")
