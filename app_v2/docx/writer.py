"""Ghi các segment/chunk đã tái cấu trúc thành Word có cấu trúc sạch.

Chỉ xử lý text; chưa xử lý ảnh, caption, bảng, hay dịch.
"""

from __future__ import annotations

from collections.abc import Sequence
import re

from docx import Document
from docx.enum.style import WD_STYLE_TYPE

from app_v2.domain.models import TextChunk, TextSegment

# Các kind segment được tái cấu trúc từ PDF text layer.
_HEADING_KINDS = {"heading"}
_PARAGRAPH_KINDS = {"paragraph"}
_BULLET_KINDS = {"bullet"}
_NUMBERED_KINDS = {"numbered_list"}
_CAPTION_KINDS = {"caption"}
# Loại bỏ: running header/footer, metadata đầu chương, page number, whitespace.
_SKIP_KINDS = {"page_marker", "whitespace", "empty", "table_like", "running_header", "metadata"}

# Heuristic đơn giản để chọn cấp heading khi segment không có level.
_HEADING_LEVEL_RE = re.compile(r"^\s*(?:chapter|ch\.?|part|section|sec\.?)\s+(\d+)", re.IGNORECASE)

# Dấu hiệu cho thấy một dòng không phải heading thật.
_NOT_HEADING_RE = re.compile(
    r"(?:©|@|https?://|www\.|\.com|\.org|\.edu|\.gov|\(ed\.?\)|\(eds?\.?\)|"
    r"doi:|e-mail|email:|tel:|fax:|fig\.|table\s*\d|et\s+al\.)",
    re.IGNORECASE,
)
_MAX_HEADING_WORDS = 12


class DocxWriter:
    """Tạo Document mới và ghi segment/chunk theo thứ tự, giữ nguyên nội dung."""

    def __init__(self) -> None:
        self._document = Document()
        self._ensure_styles()

    @property
    def document(self) -> Document:
        return self._document

    def write_segments(self, segments: Sequence[TextSegment]) -> None:
        """Ghi danh sách segment đã tái cấu trúc (thứ tự giữ nguyên)."""
        for segment in segments:
            self._write_segment(segment)

    def write_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Ghi danh sách chunk (thứ tự giữ nguyên)."""
        for chunk in chunks:
            self._write_text(chunk.text, kind="paragraph")

    def save(self, path: str) -> None:
        self._document.save(path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_styles(self) -> None:
        """Đảm bảo các style Heading 1-3, Normal và Caption tồn tại."""
        styles = self._document.styles
        for name in ("Heading 1", "Heading 2", "Heading 3", "Normal", "Caption"):
            if name not in styles:
                styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)

    def _write_segment(self, segment: TextSegment) -> None:
        kind = segment.kind
        if kind in _SKIP_KINDS:
            return
        if kind in _HEADING_KINDS:
            self._write_heading(segment.text)
            return
        if kind in _BULLET_KINDS:
            self._write_bullet(segment.text)
            return
        if kind in _NUMBERED_KINDS:
            self._write_numbered(segment.text)
            return
        if kind in _CAPTION_KINDS:
            self._write_caption(segment.text)
            return
        if kind in _PARAGRAPH_KINDS:
            self._write_paragraph(segment.text)
            return
        # Fallback: ghi như paragraph bình thường.
        self._write_paragraph(segment.text)

    def _write_heading(self, text: str) -> None:
        if not self._is_valid_heading(text):
            self._write_paragraph(text)
            return
        level = self._heading_level(text)
        self._document.add_paragraph(text, style=f"Heading {level}")

    def _write_paragraph(self, text: str) -> None:
        if text.strip():
            self._document.add_paragraph(text, style="Normal")

    def _write_caption(self, text: str) -> None:
        if text.strip():
            self._document.add_paragraph(text, style="Caption")

    def _write_bullet(self, text: str) -> None:
        if text.strip():
            self._document.add_paragraph(text, style="List Bullet")

    def _write_numbered(self, text: str) -> None:
        if text.strip():
            self._document.add_paragraph(text, style="List Number")

    def _write_text(self, text: str, kind: str) -> None:
        if kind in _HEADING_KINDS:
            self._write_heading(text)
        elif kind in _BULLET_KINDS:
            self._write_bullet(text)
        elif kind in _NUMBERED_KINDS:
            self._write_numbered(text)
        else:
            self._write_paragraph(text)

    @staticmethod
    def _is_valid_heading(text: str) -> bool:
        """Lọc các dòng bị phân loại nhầm thành heading (tên tác giả, địa chỉ, ...)."""
        stripped = text.strip()
        if not stripped:
            return False
        if len(stripped.split()) > _MAX_HEADING_WORDS:
            return False
        if _NOT_HEADING_RE.search(stripped):
            return False
        return True

    @staticmethod
    def _heading_level(text: str) -> int:
        """Chọn cấp heading dựa trên heuristic đơn giản.

        - Có từ khóa chapter/part/section + số → Heading 1
        - Toàn chữ hoa hoặc rất ngắn → Heading 1
        - Có số thập phân (1.2, 2.3) → Heading 2
        - Còn lại → Heading 3
        """
        stripped = text.strip()
        if not stripped:
            return 1
        if _HEADING_LEVEL_RE.match(stripped):
            return 1
        if re.match(r"^\d+\.\d+", stripped):
            return 2
        if stripped.isupper() or len(stripped.split()) <= 4:
            return 1
        return 3