"""Tái cấu trúc page TextBlock thành các segment có nguồn truy vết được."""

from collections import Counter
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
    _caption = re.compile(r"^\s*(?:fig(?:ure)?\.?|table|tab\.)\s*\d+", re.IGNORECASE)
    _running_header_with_page = re.compile(
        r"^\s*\d+\s+[A-Z][\w\s.,'-]+$|^[A-Z][\w\s.,'-]+\s+\d+\s*$"
    )
    _page_number_prefix = re.compile(r"^\s*\d+\s+[A-Z]")
    _page_number_suffix = re.compile(r"[A-Za-z]\s+\d+\s*$")
    _multi_space = re.compile(r"\s{2,}")
    _metadata_marker = re.compile(
        r"(?:©|copyright|https?://|www\.|doi:|springer|"
        r"all rights reserved|printed in|isbn)",
        re.IGNORECASE,
    )
    _author_marker = re.compile(
        r"(?:\(ed\.?\)|\(eds?\.?\)|\(editors?\)|\(eds\)|"
        r"e-mail|email:|tel:|fax:|university|college|institute|"
        r"department|center|centre|hospital|clinic|md\b|phd\b|"
        r"professor|dr\.|nashville|usa\b)",
        re.IGNORECASE,
    )
    _not_heading_marker = re.compile(
        r"(?:©|@|https?://|www\.|\.com|\.org|\.edu|\.gov|\(ed\.?\)|\(eds?\.?\)|"
        r"doi:|e-mail|email:|tel:|fax:|fig\.|table\s*\d|et\s+al\.|"
        r"university|college|institute|department|center|centre|hospital|clinic)",
        re.IGNORECASE,
    )

    def __init__(self, normalizer: TextNormalizer | None = None) -> None:
        self._normalizer = normalizer or TextNormalizer()

    def reconstruct(self, page_blocks: Sequence[TextBlock]) -> list[TextSegment]:
        """Giữ nguyên thứ tự và raw text; không ghép mù toàn bộ chapter."""
        # Bước 1: phát hiện running header/footer lặp lại.
        repeated_lines = self._detect_repeated_lines(page_blocks)

        segments: list[TextSegment] = []
        for block in page_blocks:
            page_segments = self._reconstruct_page(block, repeated_lines)
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

    # ------------------------------------------------------------------
    # Running header/footer detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_repeated_lines(page_blocks: Sequence[TextBlock]) -> set[str]:
        """Tìm dòng lặp lại ở vị trí đầu/cuối của nhiều trang (running header/footer)."""
        if len(page_blocks) < 3:
            return set()

        first_lines: Counter[str] = Counter()
        last_lines: Counter[str] = Counter()
        for block in page_blocks:
            lines = [line.strip() for line in block.text.splitlines() if line.strip()]
            if not lines:
                continue
            first_lines[lines[0]] += 1
            last_lines[lines[-1]] += 1

        repeated: set[str] = set()
        threshold = max(2, len(page_blocks) // 2)
        for line, count in first_lines.items():
            if count >= threshold and TextReconstructor._is_running_line(line):
                repeated.add(line)
        for line, count in last_lines.items():
            if count >= threshold and TextReconstructor._is_running_line(line):
                repeated.add(line)
        return repeated

    @staticmethod
    def _is_running_line(line: str) -> bool:
        """Dòng running header/footer thường ngắn, có page number hoặc tên tác giả."""
        if TextReconstructor._page_marker.fullmatch(line):
            return True
        if TextReconstructor._running_header_with_page.match(line):
            return True
        # Dòng có page number ở đầu hoặc cuối (ví dụ "1 Imaging in Interventional Pain Management").
        if TextReconstructor._page_number_prefix.match(line) or TextReconstructor._page_number_suffix.search(line):
            return True
        if len(line.split()) <= 8:
            return True
        return False

    # ------------------------------------------------------------------
    # Page reconstruction
    # ------------------------------------------------------------------

    def _reconstruct_page(
        self, block: TextBlock, repeated_lines: set[str]
    ) -> list[TextSegment]:
        if not block.text:
            return [self._segment("empty", "", block, 0, 0)]

        lines = block.text.splitlines(keepends=True)
        non_empty_indices = [
            index for index, line in enumerate(lines)
            if line.strip() and self._page_marker.search(line.strip()) is None
        ]
        first_content_index = non_empty_indices[0] if non_empty_indices else None
        last_content_index = non_empty_indices[-1] if non_empty_indices else None

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
        for index, line in enumerate(lines):
            line_end = offset + len(line)
            visible = line.rstrip("\r\n")
            stripped = visible.strip()

            if not stripped:
                flush_paragraph()
                segments.append(self._segment("whitespace", line, block, offset, line_end))
            elif stripped in repeated_lines or self._is_running_position(
                stripped, index, first_content_index, last_content_index
            ):
                # Running header/footer lặp lại hoặc ở vị trí đầu/cuối trang → loại bỏ.
                flush_paragraph()
                segments.append(self._segment("running_header", line, block, offset, line_end))
            else:
                kind = self._classify_line(stripped)
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

    @classmethod
    def _is_running_position(
        cls,
        stripped: str,
        index: int,
        first_content_index: int | None,
        last_content_index: int | None,
    ) -> bool:
        """Dòng đầu/cuối trang có dạng running header/footer (page + title, tên tác giả)."""
        if index == first_content_index:
            return bool(
                cls._page_marker.fullmatch(stripped)
                or cls._running_header_with_page.match(stripped)
                or cls._page_number_prefix.match(stripped)
            )
        if index == last_content_index:
            return bool(
                cls._page_marker.fullmatch(stripped)
                or cls._page_number_suffix.search(stripped)
                or cls._page_number_prefix.match(stripped)
            )
        return False

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

    def _classify_line(self, stripped: str) -> str:
        if self._page_marker.fullmatch(stripped):
            return "page_marker"
        if self._metadata_marker.search(stripped):
            return "metadata"
        # Chuẩn hóa khoảng trắng lớn (layout mode) trước khi match caption.
        normalized = self._multi_space.sub(" ", stripped).strip()
        if self._caption.match(normalized):
            return "caption"
        if self._bullet.match(stripped):
            return "bullet"
        if self._numbered_list.match(stripped):
            return "numbered_list"
        if self._is_table_like(stripped):
            return "table_like"
        if self._is_heading(stripped):
            return "heading"
        return "paragraph"

    @staticmethod
    def _is_table_like(line: str) -> bool:
        if "\t" in line or "|" in line:
            return True
        # Layout mode tạo khoảng trắng lớn giữa các cột bảng.
        # Đếm số "cụm" từ tách bởi khoảng trắng ≥ 2.
        parts = [part for part in re.split(r"\s{2,}", line.strip()) if part.strip()]
        return len(parts) >= 3

    @staticmethod
    def _is_heading(stripped: str) -> bool:
        if len(stripped) > 120 or stripped.endswith((".", "!", "?", ";", ":")):
            return False
        if TextReconstructor._not_heading_marker.search(stripped):
            return False
        words = stripped.split()
        if not 1 <= len(words) <= 12:
            return False
        capitalized = sum(word[:1].isupper() for word in words if word)
        # Cần ít nhất 2 từ viết hoa để tránh nhầm tên tác giả/địa chỉ.
        if capitalized < 2:
            return False
        # Tên tác giả thường 2-3 từ, tất cả viết hoa chữ đầu → không phải heading.
        if len(words) <= 3 and capitalized == len(words):
            return False
        return capitalized >= max(2, (len(words) + 1) // 2)

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