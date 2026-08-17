"""Adapter đọc PDF dự kiến dùng pypdf.

``pypdf`` được chọn vì hỗ trợ metadata, trích text và outline PDF. Dependency
được import trễ để Giai đoạn 1 vẫn chạy khi package này chưa được cài.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PdfDependencyError(RuntimeError):
    """Báo rõ dependency PDF cần được bổ sung trước khi đọc file."""


@dataclass(frozen=True, slots=True)
class _TextSpan:
    """Một span text với vị trí (x, y) trên trang PDF."""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float


class PypdfReader:
    """Adapter stateful bao quanh ``pypdf.PdfReader`` sau khi mở một file."""

    def __init__(self) -> None:
        self._reader: Any | None = None
        self._document: Any | None = None

    @property
    def document(self) -> Any:
        if self._document is None:
            raise RuntimeError("Chưa mở PDF")
        return self._document

    def open(self, path: Path) -> Any:
        pdf_path = Path(path)
        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)
        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]
        except ImportError as exc:
            raise PdfDependencyError(
                "Cần cài dependency 'pypdf' trước khi sử dụng PDF Reader."
            ) from exc

        self._reader = PdfReader(str(pdf_path))
        metadata = {
            str(key).lstrip("/"): str(value)
            for key, value in (self._reader.metadata or {}).items()
            if value is not None
        }
        has_text_layer = any(self.extract_page_text(i).strip() for i in range(len(self._reader.pages)))
        self._document = {
            "path": pdf_path,
            "page_count": len(self._reader.pages),
            "has_text_layer": has_text_layer,
            "metadata": metadata,
        }
        return self._document

    def extract_page_text(self, page_index: int) -> str:
        """Trích text của trang, giữ đúng thứ tự cột (trái → phải, từng cột từ trên → dưới)."""
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        if not 0 <= page_index < len(self._reader.pages):
            raise IndexError(f"Trang không hợp lệ: {page_index}")

        page = self._reader.pages[page_index]
        spans: list[TextSpan] = []

        def visitor(text: str, cm: Any, tm: Any, font_dict: Any, font_size: float) -> None:
            if not text.strip():
                return
            # tm[4] = x, tm[5] = y (PDF coordinate, y grows upward)
            x0 = tm[4]
            y0 = tm[5]
            # Estimate width from font size and text length.
            width = len(text) * (font_size or 6) * 0.5
            spans.append(TextSpan(text=text, x0=x0, y0=y0, x1=x0 + width, y1=y0 + font_size))

        page.extract_text(visitor_text=visitor)

        if not spans:
            return ""

        # Nhóm spans vào cột theo x-position.
        # Cột trái: x0 < mid_x, cột phải: x0 >= mid_x.
        min_x = min(span.x0 for span in spans)
        max_x = max(span.x1 for span in spans)
        mid_x = (min_x + max_x) / 2

        left_col = [span for span in spans if span.x0 < mid_x]
        right_col = [span for span in spans if span.x0 >= mid_x]

        # Sắp theo y (top to bottom: y lớger = higher on page).
        left_col.sort(key=lambda s: (-s.y0, s.x0))
        right_col.sort(key=lambda s: (-s.y0, s.x0))

        # Đọc cột trái trước, rồi cột phải.
        ordered = left_col + right_col

        # Ghép dòng: spans với y0 близко (same line) → join with space.
        lines: list[str] = []
        current_line: list[str] = []
        current_y: float | None = None
        for span in ordered:
            if current_y is None or abs(span.y0 - current_y) < 2.0:
                current_line.append(span.text)
                current_y = span.y0
            else:
                lines.append(" ".join(current_line))
                current_line = [span.text]
                current_y = span.y0
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def raw_outline(self) -> list[Any]:
        """Cung cấp outline thô cho parser mà không lộ ra ngoài domain."""
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        return list(self._reader.outline)

    def page_index_for_destination(self, destination: Any) -> int:
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        return self._reader.get_destination_page_number(destination)