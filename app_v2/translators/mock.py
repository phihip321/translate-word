"""Provider nội bộ dùng để kiểm thử pipeline, không thực hiện network I/O."""

from app_v2.domain.models import TextChunk, TranslatedChunk
from .base import AITranslator


class MockTranslator(AITranslator):
    provider = "mock"

    def __init__(self, model: str = "mock-echo-v1") -> None:
        self.model = model

    def translate(self, chunk: TextChunk) -> TranslatedChunk:
        return TranslatedChunk(
            chunk_id=chunk.chunk_id,
            chapter=chunk.chapter,
            sequence=chunk.sequence,
            source_text=chunk.text,
            translated_text=chunk.text,
            source_segment_indices=chunk.segment_indices,
            source_spans=chunk.source_spans,
            provider=self.provider,
            model=self.model,
            status="completed",
        )
