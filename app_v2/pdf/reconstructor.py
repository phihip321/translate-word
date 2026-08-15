"""Tái cấu trúc page TextBlock thành các segment có nguồn truy vết được."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
import re

from app_v2.domain.models import SourceSpan, TextBlock, TextSegment
from .normalizer import TextNormalizer


@dataclass(frozen=True, slots=True)
class ContentPreservationReport:
    """So sánh text nguồn với bản nguồn lưu trong các segment."""

    source_characters: int
    reconstructed_raw_characters: int
    normalized_characters: int
    is_exactly_preserved: bool


class TextReconstructor:
    """Nhóm từng trang trước, rồi chỉ ghép paragraph qua trang khi có dấu hiệu rõ."""

    _bullet = re.compile(r"^\s*(?:[-*•‣▪◦]|[–—])\s+")
    _numbered_list = re.compile(r"^\s*(?:\d+|[A-Za-z])[.)]\s+")
    _page_marker = re.compile(r"^\s*\d+\s*$")

    def __init__(self, normalizer: TextNormalizer | None = None) -> None:
        self._normalizer = normalizer or TextNormalizer()

    def reconstruct(self, page_blocks: Sequence[TextBlock]) -> list[TextSegment]:
        """Giữ nguyên thứ tự và raw text; không ghép mù toàn bộ chapter."""
        segments: list[TextSegment] = []
        for block in page_blocks:
            page_segments = self._reconstruct_page(block)
            if segments and page_segments and self._can_merge_across_pages(segments[-1], page_segments[0]):
                segments[-1] = self._merge_paragraphs(segments[-1], page_segments.pop(0))
            segments.extend(page_segments)
        return [replace(segment, index=index) for index, segment in enumerate(segments)]

    def audit(
        self, page_blocks: Sequence[TextBlock], segments: Sequence[TextSegment]
    ) -> ContentPreservationReport:
        source_text = "".join(block.text for block in page_blocks)
        reconstructed_raw_text = "".join(segment.raw_text for segment in segments)
        return ContentPreservationReport(
            source_characters=len(source_text),
            reconstructed_raw_characters=len(reconstructed_raw_text),
            normalized_characters=sum(len(segment.text) for segment in segments),
            is_exactly_preserved=source_text == reconstructed_raw_text,
        )

    def _reconstruct_page(self, block: TextBlock) -> list[TextSegment]:
        if not block.text:
            return [self._segment("empty", "", block, 0, 0)]

        segments: list[TextSegment] = []
        paragraph_start: int | None = None
        paragraph_parts: list[str] = []

        def flush_paragraph() -> None:
            nonlocal paragraph_start, paragraph_parts
            if paragraph_start is not None:
                raw_text = "".join(paragraph_parts)
                segments.append(
                    self._segment("paragraph", raw_text, block, paragraph_start, paragraph_start + len(raw_text))
                )
            paragraph_start, paragraph_parts = None, []

        offset = 0
        for line in block.text.splitlines(keepends=True):
            line_end = offset + len(line)
            visible = line.rstrip("\r\n")
            if not visible.strip():
                flush_paragraph()
                segments.append(self._segment("whitespace", line, block, offset, line_end))
            else:
                kind = self._classify_line(visible)
                if kind == "paragraph":
                    if paragraph_start is None:
                        paragraph_start = offset
                    paragraph_parts.append(line)
                else:
                    flush_paragraph()
                    segments.append(self._segment(kind, line, block, offset, line_end))
            offset = line_end
        flush_paragraph()
        return segments

    def _segment(
        self, kind: str, raw_text: str, block: TextBlock, start: int, end: int
    ) -> TextSegment:
        return TextSegment(
            index=0,
            kind=kind,
            text=self._normalizer.normalize(raw_text, kind),
            raw_text=raw_text,
            source_spans=(SourceSpan(block.page_index, start, end),),
            chapter=block.chapter,
        )

    def _classify_line(self, line: str) -> str:
        stripped = line.strip()
        if self._page_marker.fullmatch(line):
            return "page_marker"
        if self._bullet.match(line):
            return "bullet"
        if self._numbered_list.match(line):
            return "numbered_list"
        if self._is_table_like(line):
            return "table_like"
        if self._is_heading(stripped):
            return "heading"
        return "paragraph"

    @staticmethod
    def _is_table_like(line: str) -> bool:
        return "\t" in line or "|" in line or bool(re.search(r"\S {2,}\S {2,}\S", line))

    @staticmethod
    def _is_heading(stripped: str) -> bool:
        if len(stripped) > 120 or stripped.endswith((".", "!", "?", ";", ":")):
            return False
        words = stripped.split()
        if not 1 <= len(words) <= 16:
            return False
        capitalized = sum(word[:1].isupper() for word in words if word)
        return capitalized >= max(1, (len(words) + 1) // 2)

    def _can_merge_across_pages(self, previous: TextSegment, following: TextSegment) -> bool:
        if previous.kind != "paragraph" or following.kind != "paragraph":
            return False
        if previous.source_spans[-1].page_index + 1 != following.source_spans[0].page_index:
            return False
        previous_text = previous.raw_text.rstrip()
        following_text = following.raw_text.lstrip()
        return bool(
            previous_text
            and following_text
            and previous_text[-1] not in ".!?;:"
            and following_text[0].islower()
        )

    def _merge_paragraphs(self, previous: TextSegment, following: TextSegment) -> TextSegment:
        raw_text = previous.raw_text + following.raw_text
        return TextSegment(
            index=previous.index,
            kind="paragraph",
            text=self._normalizer.normalize(raw_text, "paragraph"),
            raw_text=raw_text,
            source_spans=previous.source_spans + following.source_spans,
            chapter=previous.chapter,
        )
