"""Interface duy nhất giữa TranslationManager và mọi AI provider."""

from abc import ABC, abstractmethod

from app_v2.domain.models import TextChunk, TranslatedChunk


class ProviderNotAvailableError(RuntimeError):
    """Provider skeleton chưa được phép gọi API ở giai đoạn hiện tại."""


class AITranslator(ABC):
    provider: str
    model: str

    @abstractmethod
    def translate(self, chunk: TextChunk) -> TranslatedChunk:
        """Dịch một chunk mà không thay đổi metadata nguồn."""
