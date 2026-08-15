"""Gemini provider độc lập, dùng chung AITranslator interface."""

import os

from google import genai

from app_v2.domain.models import TextChunk, TranslatedChunk
from .base import AITranslator


class GeminiConfigurationError(RuntimeError):
    """Thiếu cấu hình Gemini cục bộ; không tiết lộ bất kỳ giá trị bí mật nào."""


class GeminiTranslationError(RuntimeError):
    """Lỗi API Gemini, giữ nguyên exception gốc trong chuỗi nguyên nhân."""


class GeminiTranslator(AITranslator):
    provider = "gemini"

    def __init__(
        self,
        model: str,
        source_language: str = "English",
        target_language: str = "Vietnamese",
    ) -> None:
        self.model = model
        self.source_language = source_language
        self.target_language = target_language
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is not set in the environment.")
        self._client = genai.Client(api_key=api_key)

    def translate(self, chunk: TextChunk) -> TranslatedChunk:
        prompt = f"""Bạn là biên dịch viên chuyên ngành y khoa.
Dịch từ {self.source_language} sang {self.target_language}.
Giữ nguyên ý nghĩa chuyên môn.
Không giải thích.
Chỉ trả về bản dịch.
Không thêm lời mở đầu/kết luận.

Văn bản:
{chunk.text}"""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            translated_text = (response.text or "").strip()
        except Exception as exc:
            raise GeminiTranslationError(
                f"Gemini request failed ({type(exc).__name__}): {exc}"
            ) from exc
        if not translated_text:
            raise GeminiTranslationError("Gemini returned an empty translation.")
        return TranslatedChunk(
            chunk_id=chunk.chunk_id,
            chapter=chunk.chapter,
            sequence=chunk.sequence,
            source_text=chunk.text,
            translated_text=translated_text,
            source_segment_indices=chunk.segment_indices,
            source_spans=chunk.source_spans,
            provider=self.provider,
            model=self.model,
            status="completed",
        )
