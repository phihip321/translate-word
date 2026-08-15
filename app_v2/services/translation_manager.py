"""Điều phối dịch qua interface chung và xác minh mapping đầu vào/đầu ra."""

from collections.abc import Sequence

from app_v2.domain.contracts import AITranslatorContract
from app_v2.domain.models import TextChunk, TranslatedChunk


class TranslationValidationError(ValueError):
    """Kết quả provider không còn khớp tuyệt đối với source chunk."""


class TranslationManager:
    """Không biết API Gemini/OpenAI/DeepSeek; chỉ gọi AITranslatorContract."""

    def __init__(self, translator: AITranslatorContract) -> None:
        self._translator = translator

    def translate(self, chunks: Sequence[TextChunk]) -> list[TranslatedChunk]:
        self._validate_input(chunks)
        translated = [self._translator.translate(chunk) for chunk in chunks]
        self._validate_output(chunks, translated)
        return translated

    @staticmethod
    def _validate_input(chunks: Sequence[TextChunk]) -> None:
        identifiers = [chunk.chunk_id for chunk in chunks]
        sequences = [chunk.sequence for chunk in chunks]
        if len(identifiers) != len(set(identifiers)):
            raise TranslationValidationError("Duplicate chunk_id in input")
        if len(sequences) != len(set(sequences)):
            raise TranslationValidationError("Duplicate sequence in input")
        if sequences != list(range(1, len(chunks) + 1)):
            raise TranslationValidationError("Missing or out-of-order chunk sequence")

    def _validate_output(
        self, source_chunks: Sequence[TextChunk], translated: Sequence[TranslatedChunk]
    ) -> None:
        if len(translated) != len(source_chunks):
            raise TranslationValidationError("Missing or extra translated chunks")
        seen_ids: set[str] = set()
        for source, output in zip(source_chunks, translated, strict=True):
            if output.chunk_id in seen_ids:
                raise TranslationValidationError("Duplicate chunk_id in output")
            seen_ids.add(output.chunk_id)
            if output.chunk_id != source.chunk_id or output.sequence != source.sequence:
                raise TranslationValidationError("chunk_id or sequence order changed")
            if output.chapter != source.chapter:
                raise TranslationValidationError("chapter mapping changed")
            if output.source_text != source.text:
                raise TranslationValidationError("source_text changed")
            if output.source_segment_indices != source.segment_indices or output.source_spans != source.source_spans:
                raise TranslationValidationError("source mapping changed")
            if output.provider != self._translator.provider or output.model != self._translator.model:
                raise TranslationValidationError("provider or model metadata changed")
            if not output.status:
                raise TranslationValidationError("translation status is empty")
