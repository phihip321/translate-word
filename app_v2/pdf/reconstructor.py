"""Tái cấu trúc text PDF thành các segment có truy vết nguồn.

Mục tiêu:
- Giữ nguyên raw_text để audit.
- Không OCR.
- Không dịch.
- Không tự ý làm mất nội dung.
- Gom các dòng PDF thành paragraph hợp lý.
- Không cắt paragraph chỉ vì một dòng PDF kết thúc bằng dấu chấm.
- Giữ heading / caption / list / reference / metadata riêng.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
import re

from app_v2.domain.models import SourceSpan, TextBlock, TextSegment
from .normalizer import TextNormalizer


@dataclass(frozen=True, slots=True)
class ContentPreservationReport:
    """Báo cáo bảo toàn text nguồn."""

    source_characters: int
    reconstructed_raw_characters: int
    normalized_characters: int
    is_exactly_preserved: bool


class TextReconstructor:
    """
    Tái cấu trúc TextBlock thành TextSegment.

    Nguyên tắc:

    PDF text
        ↓
    structural segments
        ↓
    paragraph / heading / caption / reference / metadata
        ↓
    ParagraphChunker

    raw_text luôn được giữ lại.

    QUAN TRỌNG:
    Không dùng heuristic quá mạnh để cắt paragraph.
    PDF thường xuống dòng giữa một câu.
    """

    # ---------------------------------------------------------
    # BASIC PATTERNS
    # ---------------------------------------------------------

    _bullet = re.compile(
        r"^\s*(?:[-*•‣▪◦]|[–—])\s+"
    )

    _numbered_list = re.compile(
        r"^\s*(?:\d+|[A-Za-z])[.)]\s+"
    )

    _page_marker = re.compile(
        r"^\s*\d+\s*$"
    )

    _caption = re.compile(
        r"^\s*(?:fig(?:ure)?\.?|table|tab\.)\s*"
        r"\d+(?:[A-Za-z])?",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # METADATA
    # ---------------------------------------------------------

    _metadata_marker = re.compile(
        r"(?:"
        r"©|copyright|https?://|www\.|doi:|"
        r"all rights reserved|printed in|isbn"
        r")",
        re.IGNORECASE,
    )

    _contact_marker = re.compile(
        r"(?:"
        r"e-mail|email:|tel:|fax:"
        r")",
        re.IGNORECASE,
    )

    _institution_marker = re.compile(
        r"(?:"
        r"\buniversity\b|"
        r"\bcollege\b|"
        r"\bdepartment\b|"
        r"\binstitute\b|"
        r"\bcenter\b|"
        r"\bcentre\b|"
        r"\bhospital\b|"
        r"\bclinic\b|"
        r"\bschool\b"
        r")",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # REFERENCES
    # ---------------------------------------------------------

    _reference_marker = re.compile(
        r"^\s*(?:"
        r"\d{1,3}[.)]\s+"
        r"|"
        r"\[\d{1,3}\]\s+"
        r")"
    )

    _reference_tail = re.compile(
        r"\b(?:"
        r"J\s+Pain|"
        r"Pain\s+Physician|"
        r"Reg\s+Anesth|"
        r"Anesth\s+Analg|"
        r"J\s+Ultrasound\s+Med|"
        r"Clin\s+J\s+Pain|"
        r"Arch\s+Phys\s+Med\s+Rehabil|"
        r"N\s+Engl\s+J\s+Med|"
        r"Anesthesiology|"
        r"Med\s+Phys|"
        r"J\s+Vasc\s+Interv\s+Radiol"
        r")\b",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # SENTENCE / ABBREVIATION
    # ---------------------------------------------------------

    _sentence_end = re.compile(
        r'[.!?]["\')\]]?$'
    )

    _abbreviation_end = re.compile(
        r"(?:"
        r"\b(?:"
        r"Dr|Mr|Mrs|Ms|Prof|Fig|Figs|"
        r"approx|vs|etc|i\.e|e\.g"
        r")\."
        r")$",
        re.IGNORECASE,
    )

    _multi_space = re.compile(
        r"\s{2,}"
    )

    # ---------------------------------------------------------
    # HEADING
    # ---------------------------------------------------------

    _heading_word = re.compile(
        r"^(?:"
        r"introduction|background|objective|objectives|"
        r"methods?|materials\s+and\s+methods?|"
        r"results?|discussion|conclusion|"
        r"references?|acknowledg(?:e)?ments?|"
        r"case\s+report|case\s+reports?|"
        r"technique|techniques|"
        r"indications?|contraindications?|"
        r"complications?|anatomy|"
        r"clinical\s+applications?|"
        r"ultrasound|"
        r"fluoroscopy|"
        r"computed\s+tomography|"
        r"c-arm|"
        r"advantages?|disadvantages?|"
        r"limitations?|summary"
        r")$",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # INIT
    # ---------------------------------------------------------

    def __init__(
        self,
        normalizer: TextNormalizer | None = None,
    ) -> None:
        self._normalizer = normalizer or TextNormalizer()

    # =========================================================
    # PUBLIC
    # =========================================================

    def reconstruct(
        self,
        page_blocks: Sequence[TextBlock],
    ) -> list[TextSegment]:
        """
        Tái cấu trúc toàn bộ PDF theo thứ tự trang.

        Không làm mất raw text.
        """

        repeated_lines = self._detect_repeated_lines(
            page_blocks
        )

        segments: list[TextSegment] = []

        for block in page_blocks:

            page_segments = self._reconstruct_page(
                block,
                repeated_lines,
            )

            # Chỉ nối paragraph qua trang khi thật sự có dấu hiệu
            # paragraph bị cắt giữa câu.
            if (
                segments
                and page_segments
                and self._can_merge_across_pages(
                    segments[-1],
                    page_segments[0],
                )
            ):
                segments[-1] = self._merge_paragraphs(
                    segments[-1],
                    page_segments.pop(0),
                )

            segments.extend(page_segments)

        return [
            replace(segment, index=index)
            for index, segment in enumerate(segments)
        ]

    # =========================================================
    # AUDIT
    # =========================================================

    def audit(
        self,
        page_blocks: Sequence[TextBlock],
        segments: Sequence[TextSegment],
    ) -> ContentPreservationReport:
        """Kiểm tra raw text có bị mất hay không."""

        source_text = "".join(
            block.text
            for block in page_blocks
        )

        reconstructed_raw_text = "".join(
            segment.raw_text
            for segment in segments
        )

        return ContentPreservationReport(
            source_characters=len(source_text),
            reconstructed_raw_characters=len(
                reconstructed_raw_text
            ),
            normalized_characters=sum(
                len(segment.text)
                for segment in segments
            ),
            is_exactly_preserved=(
                source_text == reconstructed_raw_text
            ),
        )

    # =========================================================
    # PAGE
    # =========================================================

    def _reconstruct_page(
        self,
        block: TextBlock,
        repeated_lines: set[str],
    ) -> list[TextSegment]:

        if not block.text:
            return [
                self._segment(
                    "empty",
                    "",
                    block,
                    0,
                    0,
                )
            ]

        lines = block.text.splitlines(
            keepends=True
        )

        non_empty_indices = [
            index
            for index, line in enumerate(lines)
            if (
                line.strip()
                and not self._page_marker.fullmatch(
                    line.strip()
                )
            )
        ]

        first_content_index = (
            non_empty_indices[0]
            if non_empty_indices
            else None
        )

        last_content_index = (
            non_empty_indices[-1]
            if non_empty_indices
            else None
        )

        segments: list[TextSegment] = []

        paragraph_parts: list[str] = []
        paragraph_start: int | None = None

        def flush_paragraph() -> None:
            nonlocal paragraph_parts
            nonlocal paragraph_start

            if paragraph_start is None:
                return

            raw_text = "".join(
                paragraph_parts
            )

            if raw_text.strip():
                segments.append(
                    self._segment(
                        "paragraph",
                        raw_text,
                        block,
                        paragraph_start,
                        paragraph_start + len(raw_text),
                    )
                )

            paragraph_parts = []
            paragraph_start = None

        offset = 0

        for index, line in enumerate(lines):

            line_end = offset + len(line)

            visible = line.rstrip(
                "\r\n"
            )

            stripped = visible.strip()

            # -------------------------------------------------
            # BLANK LINE
            # -------------------------------------------------

            if not stripped:

                flush_paragraph()

                segments.append(
                    self._segment(
                        "whitespace",
                        line,
                        block,
                        offset,
                        line_end,
                    )
                )

                offset = line_end
                continue

            # -------------------------------------------------
            # RUNNING HEADER / FOOTER
            # -------------------------------------------------

            if (
                stripped in repeated_lines
                or self._is_running_position(
                    stripped,
                    index,
                    first_content_index,
                    last_content_index,
                )
            ):

                flush_paragraph()

                segments.append(
                    self._segment(
                        "running_header",
                        line,
                        block,
                        offset,
                        line_end,
                    )
                )

                offset = line_end
                continue

            # -------------------------------------------------
            # CLASSIFY
            # -------------------------------------------------

            kind = self._classify_line(
                stripped
            )

            if kind != "paragraph":

                flush_paragraph()

                segments.append(
                    self._segment(
                        kind,
                        line,
                        block,
                        offset,
                        line_end,
                    )
                )

                offset = line_end
                continue

            # -------------------------------------------------
            # PARAGRAPH
            # -------------------------------------------------

            if paragraph_start is None:

                paragraph_start = offset
                paragraph_parts = [line]

            else:

                previous_line = (
                    paragraph_parts[-1]
                    .rstrip("\r\n")
                    .strip()
                )

                if self._should_start_new_paragraph(
                    previous_line,
                    stripped,
                ):

                    flush_paragraph()

                    paragraph_start = offset
                    paragraph_parts = [line]

                else:

                    paragraph_parts.append(line)

            offset = line_end

        flush_paragraph()

        return segments

    # =========================================================
    # PARAGRAPH DETECTION
    # =========================================================

    @classmethod
    def _should_start_new_paragraph(
        cls,
        previous_line: str,
        current_line: str,
    ) -> bool:
        """
        Quyết định dòng hiện tại có bắt đầu paragraph mới hay không.

        Đây là heuristic bảo thủ.

        Không được tách chỉ vì:
            previous_line.endswith(".")

        vì PDF thường xuống dòng giữa paragraph.
        """

        if not previous_line:
            return False

        if not current_line:
            return False

        # -----------------------------------------------------
        # Dòng bắt đầu bằng chữ thường gần như chắc chắn
        # là continuation.
        # -----------------------------------------------------

        if current_line[0].islower():
            return False

        # -----------------------------------------------------
        # Dòng bắt đầu bằng số có thể là continuation:
        # ví dụ citation, số liệu, năm...
        # -----------------------------------------------------

        if current_line[0].isdigit():
            return False

        # -----------------------------------------------------
        # Abbreviation
        # -----------------------------------------------------

        if cls._abbreviation_end.search(
            previous_line
        ):
            return False

        # -----------------------------------------------------
        # Nếu dòng trước chưa kết thúc câu,
        # tuyệt đối không tách.
        # -----------------------------------------------------

        if not cls._sentence_end.search(
            previous_line
        ):
            return False

        # -----------------------------------------------------
        # Heading rõ ràng
        # -----------------------------------------------------

        if cls._is_heading_word(
            current_line
        ):
            return True

        # -----------------------------------------------------
        # Một số mẫu câu mới thường gặp trong sách y khoa.
        # -----------------------------------------------------

        if re.match(
            r"^(?:"
            r"The|This|These|Those|"
            r"In|For|However|Therefore|"
            r"Thus|Although|Because|"
            r"When|While|If|As|"
            r"Patients?|Methods?|Results?|"
            r"Conclusion|Figure|Table|"
            r"We|Our|An?|"
            r"Another|Several|Such|"
            r"One|Most|Many|"
            r"Ultrasound|"
            r"Fluoroscopy|"
            r"Computed|"
            r"Magnetic"
            r")\b",
            current_line,
            re.IGNORECASE,
        ):
            return True

        # -----------------------------------------------------
        # KHÔNG dùng chữ hoa đơn thuần để tách.
        #
        # Đây là điểm quan trọng.
        # -----------------------------------------------------

        return False

    # =========================================================
    # CLASSIFICATION
    # =========================================================

    def _classify_line(
        self,
        stripped: str,
    ) -> str:

        if self._page_marker.fullmatch(
            stripped
        ):
            return "page_marker"

        if self._metadata_marker.search(
            stripped
        ):
            return "metadata"

        if self._contact_marker.search(
            stripped
        ):
            return "metadata"

        if self._reference_marker.match(
            stripped
        ):
            return "reference"

        normalized = self._multi_space.sub(
            " ",
            stripped,
        ).strip()

        if self._caption.match(
            normalized
        ):
            return "caption"

        if self._bullet.match(
            stripped
        ):
            return "bullet"

        if self._numbered_list.match(
            stripped
        ):
            return "numbered_list"

        if self._is_table_like(
            stripped
        ):
            return "table_like"

        if self._is_heading(
            stripped
        ):
            return "heading"

        return "paragraph"

    # =========================================================
    # HEADING
    # =========================================================

    @classmethod
    def _is_heading_word(
        cls,
        text: str,
    ) -> bool:

        normalized = cls._multi_space.sub(
            " ",
            text,
        ).strip()

        return bool(
            cls._heading_word.fullmatch(
                normalized
            )
        )

    @classmethod
    def _is_heading(
        cls,
        stripped: str,
    ) -> bool:

        normalized = cls._multi_space.sub(
            " ",
            stripped,
        ).strip()

        if cls._is_heading_word(
            normalized
        ):
            return True

        if len(normalized) > 100:
            return False

        if normalized.endswith(
            (
                ".",
                "!",
                "?",
                ";",
                ":",
            )
        ):
            return False

        if cls._metadata_marker.search(
            normalized
        ):
            return False

        if cls._contact_marker.search(
            normalized
        ):
            return False

        if cls._institution_marker.search(
            normalized
        ):
            return False

        words = normalized.split()

        if not 1 <= len(words) <= 10:
            return False

        # Không coi câu bắt đầu bằng các từ này là heading.
        if len(words) >= 5:

            first = words[0].lower()

            if first in {
                "the",
                "this",
                "these",
                "those",
                "in",
                "for",
                "patients",
                "we",
                "our",
            }:
                return False

        capitalized = sum(
            bool(
                word
                and word[0].isupper()
            )
            for word in words
        )

        # Tên người ngắn.
        if (
            len(words) <= 3
            and capitalized == len(words)
        ):
            return False

        return (
            capitalized
            >= max(
                2,
                (len(words) + 1) // 2,
            )
        )

    # =========================================================
    # TABLE
    # =========================================================

    @classmethod
    def _is_table_like(
        cls,
        line: str,
    ) -> bool:

        if "\t" in line:
            return True

        if "|" in line:
            return True

        parts = [
            part.strip()
            for part in re.split(
                r"\s{3,}",
                line.strip(),
            )
            if part.strip()
        ]

        if len(parts) >= 3:
            return True

        words = line.split()

        if (
            len(words) >= 4
            and sum(
                word[:1].isdigit()
                for word in words
            ) >= 2
        ):
            return True

        return False

    # =========================================================
    # RUNNING HEADER / FOOTER
    # =========================================================

    @staticmethod
    def _detect_repeated_lines(
        page_blocks: Sequence[TextBlock],
    ) -> set[str]:

        if len(page_blocks) < 3:
            return set()

        first_lines: Counter[str] = Counter()
        last_lines: Counter[str] = Counter()

        for block in page_blocks:

            lines = [
                line.strip()
                for line in block.text.splitlines()
                if line.strip()
            ]

            if not lines:
                continue

            first_lines[lines[0]] += 1
            last_lines[lines[-1]] += 1

        repeated: set[str] = set()

        threshold = max(
            2,
            len(page_blocks) // 2,
        )

        for line, count in first_lines.items():

            if (
                count >= threshold
                and TextReconstructor._is_running_line(
                    line
                )
            ):
                repeated.add(line)

        for line, count in last_lines.items():

            if (
                count >= threshold
                and TextReconstructor._is_running_line(
                    line
                )
            ):
                repeated.add(line)

        return repeated

    @staticmethod
    def _is_running_line(
        line: str,
    ) -> bool:

        if TextReconstructor._page_marker.fullmatch(
            line
        ):
            return True

        words = line.split()

        # Header/footer ngắn.
        if len(words) <= 3:
            return True

        # Không tự động loại dòng dài.
        return False

    @classmethod
    def _is_running_position(
        cls,
        stripped: str,
        index: int,
        first_content_index: int | None,
        last_content_index: int | None,
    ) -> bool:

        if index == first_content_index:
            return bool(
                cls._page_marker.fullmatch(
                    stripped
                )
            )

        if index == last_content_index:
            return bool(
                cls._page_marker.fullmatch(
                    stripped
                )
            )

        return False

    # =========================================================
    # CROSS PAGE
    # =========================================================

    def _can_merge_across_pages(
        self,
        previous: TextSegment,
        following: TextSegment,
    ) -> bool:

        if previous.kind != "paragraph":
            return False

        if following.kind != "paragraph":
            return False

        if (
            previous.source_spans[-1].page_index + 1
            != following.source_spans[0].page_index
        ):
            return False

        previous_text = (
            previous.raw_text.rstrip()
        )

        following_text = (
            following.raw_text.lstrip()
        )

        if not previous_text:
            return False

        if not following_text:
            return False

        # Nếu câu đã hoàn chỉnh thì không nối.
        if previous_text[-1] in ".!?":
            return False

        # Chữ thường ở đầu trang mới → rất có khả năng
        # là phần tiếp theo của paragraph.
        if following_text[0].islower():
            return True

        # Trường hợp PDF xuống trang giữa câu.
        return (
            len(previous_text) > 50
            and not previous_text.endswith(
                (
                    ":",
                    ";",
                )
            )
        )

    def _merge_paragraphs(
        self,
        previous: TextSegment,
        following: TextSegment,
    ) -> TextSegment:

        raw_text = (
            previous.raw_text
            + following.raw_text
        )

        return TextSegment(
            index=previous.index,
            kind="paragraph",
            text=self._normalizer.normalize(
                raw_text,
                "paragraph",
            ),
            raw_text=raw_text,
            source_spans=(
                previous.source_spans
                + following.source_spans
            ),
            chapter=previous.chapter,
        )

    # =========================================================
    # SEGMENT FACTORY
    # =========================================================

    def _segment(
        self,
        kind: str,
        raw_text: str,
        block: TextBlock,
        start: int,
        end: int,
    ) -> TextSegment:

        return TextSegment(
            index=0,
            kind=kind,
            text=self._normalizer.normalize(
                raw_text,
                kind,
            ),
            raw_text=raw_text,
            source_spans=(
                SourceSpan(
                    block.page_index,
                    start,
                    end,
                ),
            ),
            chapter=block.chapter,
        )