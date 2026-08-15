"""Tạo provider từ cấu hình; TranslationManager không phụ thuộc factory này."""

from app_v2.config.settings import ProviderSettings
from .base import AITranslator
from .deepseek import DeepSeekTranslator
from .gemini import GeminiTranslator
from .mock import MockTranslator
from .openai import OpenAITranslator


def create_translator(settings: ProviderSettings) -> AITranslator:
    if settings.provider == "mock":
        return MockTranslator(settings.resolved_model)
    if settings.provider == "gemini":
        return GeminiTranslator(
            settings.resolved_model,
            source_language=settings.source_language,
            target_language=settings.target_language,
        )
    if settings.provider == "openai":
        return OpenAITranslator(settings.resolved_model)
    if settings.provider == "deepseek":
        return DeepSeekTranslator(settings.resolved_model)
    raise ValueError(f"Unsupported provider: {settings.provider}")
