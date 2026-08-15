"""Semantic chunker không overlap, dựa trên TextSegment đã tái cấu trúc."""

from collections.abc import Sequence
from dataclasses import dataclass
import re

from app_v2.config.settings import DEFAULT_MAX_CHARS
from app_v2.domain.models import Chapter, SourceSpan, TextChunk, TextSegment


@dataclass(frozen=True, slots=True)
class ChunkingReport:
    input_characters: int
    chunk_characters: int
    is_exactly_preserved: bool


@dataclass(frozen=True, slots=True)
class _Unit:
    text: str
    segment_indices: tuple[int, ...]
    source_spans: tuple[SourceSpan, ...]


class SemanticTextChunker:
    """Đóng gói segment theo giới hạn ký tự mà không lặp hay thay đổi text."""

    _sentence_boundary = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_characters: int = DEFAULT_MAX_CHARS) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters phải lớn hơn 0")
        self.max_characters = max_characters

    def chunk(self, chapter: Chapter, segments: Sequence[TextSegment]) -> list[TextChunk]:
        units = self._units_from_segments(segments)
        chunks: list[TextChunk] = []
        current: list[_Unit] = []
        current_length = 0

        def flush() -> None:
            nonlocal current, current_length
            if not current:
                return
            chunks.append(self._make_chunk(chapter, len(chunks) + 1, current))
            current, current_length = [], 0

        for unit in units:
            if len(unit.text) > self.max_characters:
                flush()
                for piece in self._split_long_unit(unit):
                    chunks.append(self._make_chunk(chapter, len(chunks) + 1, [piece]))
                continue
            if current and current_length + len(unit.text) > self.max_characters:
                flush()
            current.append(unit)
            current_length += len(unit.text)
        flush()
        return chunks

    @staticmethod
    def audit(segments: Sequence[TextSegment], chunks: Sequence[TextChunk]) -> ChunkingReport:
        input_text = "".join(segment.text for segment in segments)
        chunk_text = "".join(chunk.text for chunk in chunks)
        return ChunkingReport(
            input_characters=len(input_text),
            chunk_characters=len(chunk_text),
            is_exactly_preserved=input_text == chunk_text,
        )

    def _units_from_segments(self, segments: Sequence[TextSegment]) -> list[_Unit]:
        units: list[_Unit] = []
        index = 0
        while index < len(segments):
            segment = segments[index]
            if not segment.text:
                index += 1
                continue
            if (
                segment.kind == "heading"
                and index + 1 < len(segments)
                and segments[index + 1].kind == "paragraph"
                and segments[index + 1].text
            ):
                following = segments[index + 1]
                units.append(self._unit_from_segments((segment, following)))
                index += 2
                continue
            units.append(self._unit_from_segments((segment,)))
            index += 1
        return units

    @staticmethod
    def _unit_from_segments(segments: Sequence[TextSegment]) -> _Unit:
        spans: list[SourceSpan] = []
        for segment in segments:
            for span in segment.source_spans:
                if span not in spans:
                    spans.append(span)
        return _Unit(
            text="".join(segment.text for segment in segments),
            segment_indices=tuple(segment.index for segment in segments),
            source_spans=tuple(spans),
        )

    def _split_long_unit(self, unit: _Unit) -> list[_Unit]:
        pieces: list[_Unit] = []
        start = 0
        text = unit.text
        while len(text) - start > self.max_characters:
            limit = start + self.max_characters
            boundaries = [match.end() for match in self._sentence_boundary.finditer(text, start, limit)]
            end = boundaries[-1] if boundaries else limit
            pieces.append(self._copy_with_text(unit, text[start:end]))
            start = end
        if start < len(text):
            pieces.append(self._copy_with_text(unit, text[start:]))
        return pieces

    @staticmethod
    def _copy_with_text(unit: _Unit, text: str) -> _Unit:
        return _Unit(text=text, segment_indices=unit.segment_indices, source_spans=unit.source_spans)

    @staticmethod
    def _make_chunk(chapter: Chapter, sequence: int, units: Sequence[_Unit]) -> TextChunk:
        text = "".join(unit.text for unit in units)
        spans: list[SourceSpan] = []
        indices: list[int] = []
        for unit in units:
            for index in unit.segment_indices:
                if index not in indices:
                    indices.append(index)
            for span in unit.source_spans:
                if span not in spans:
                    spans.append(span)
        return TextChunk(
            chunk_id=f"chapter-{chapter.start_page + 1:04d}-{sequence:03d}",
            chapter=chapter,
            sequence=sequence,
            text=text,
            segment_indices=tuple(indices),
            source_spans=tuple(spans),
            char_count=len(text),
        )
