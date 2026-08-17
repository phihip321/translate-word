"""Adapter đọc PDF dùng pypdf.

Mục tiêu hiện tại:
- PDF có text layer.
- Không OCR.
- Không cố tái tạo bố cục PDF.
- Với sách 2 cột, cố gắng đưa về một luồng reading order:
  cột trái từ trên xuống dưới, sau đó cột phải.

Phần còn lại của app_v2 vẫn nhận PdfDocument như trước.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from app_v2.domain.models import PdfDocument


class PdfDependencyError(RuntimeError):
    """Báo rõ dependency PDF cần được bổ sung trước khi đọc file."""


class PypdfReader:
    """Adapter stateful bao quanh pypdf.PdfReader."""

    # Khoảng trắng lớn trong layout text thường là khoảng giữa hai cột.
    _COLUMN_GAP = re.compile(r"\s{10,}")

    def __init__(self) -> None:
        self._reader: Any | None = None
        self._document: PdfDocument | None = None

    @property
    def document(self) -> PdfDocument:
        if self._document is None:
            raise RuntimeError("Chưa mở PDF")
        return self._document

    def open(self, path: Path) -> PdfDocument:
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

        # Kiểm tra PDF có text layer hay không.
        has_text_layer = any(
            self._extract_raw_page_text(i).strip()
            for i in range(len(self._reader.pages))
        )

        self._document = PdfDocument(
            path=pdf_path,
            page_count=len(self._reader.pages),
            has_text_layer=has_text_layer,
            metadata=metadata,
        )

        return self._document

    def extract_page_text(self, page_index: int) -> str:
        """Trích text của một trang theo reading order đơn giản."""

        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")

        if not 0 <= page_index < len(self._reader.pages):
            raise IndexError(f"Trang không hợp lệ: {page_index}")

        page = self._reader.pages[page_index]

        # Ưu tiên layout mode để giữ tương đối cấu trúc cột.
        try:
            text = page.extract_text(extraction_mode="layout")
        except TypeError:
            # Tương thích với phiên bản pypdf cũ.
            text = page.extract_text()

        if not text:
            return ""

        return self._reorder_layout_text(text)

    def _extract_raw_page_text(self, page_index: int) -> str:
        """Đọc text thô chỉ để kiểm tra text layer."""

        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")

        page = self._reader.pages[page_index]

        try:
            return page.extract_text(extraction_mode="layout") or ""
        except TypeError:
            return page.extract_text() or ""

    @classmethod
    def _reorder_layout_text(cls, text: str) -> str:
        """
        Đưa layout text về một luồng đọc.

        Với trang hai cột:
            - phần đầu trang
            - cột trái từ trên xuống
            - cột phải từ trên xuống

        Với trang không nhận ra hai cột:
            giữ thứ tự layout hiện có.
        """

        raw_lines = text.splitlines()

        # Loại dòng trắng thừa ở đầu/cuối.
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)

        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()

        if not raw_lines:
            return ""

        two_column_start = cls._find_two_column_start(raw_lines)

        # Không thấy dấu hiệu hai cột.
        if two_column_start is None:
            return "\n".join(
                line.strip()
                for line in raw_lines
                if line.strip()
            )

        preamble: list[str] = []
        left_column: list[str] = []
        right_column: list[str] = []

        # Phần đầu trang trước vùng 2 cột.
        for line in raw_lines[:two_column_start]:
            stripped = line.strip()
            if stripped:
                preamble.append(stripped)

        # Phần nội dung hai cột.
        for line in raw_lines[two_column_start:]:
            if not line.strip():
                continue

            split = cls._split_columns(line)

            if split is not None:
                left, right = split

                if left:
                    left_column.append(left)

                if right:
                    right_column.append(right)

                continue

            # Dòng không có gutter rõ.
            # Layout mode thường giữ cột phải thụt sâu hơn.
            stripped = line.strip()
            leading_spaces = len(line) - len(line.lstrip())

            if leading_spaces >= 40:
                right_column.append(stripped)
            else:
                left_column.append(stripped)

        output: list[str] = []

        output.extend(preamble)

        if preamble and left_column:
            output.append("")

        output.extend(left_column)

        if left_column and right_column:
            output.append("")

        output.extend(right_column)

        return "\n".join(output)

    @classmethod
    def _find_two_column_start(cls, lines: list[str]) -> int | None:
        """
        Tìm dòng đầu tiên có dấu hiệu rõ của hai cột.

        Không coi một dòng ngắn như title hoặc metadata là hai cột.
        """

        for index, line in enumerate(lines):
            match = cls._COLUMN_GAP.search(line)

            if not match:
                continue

            left = line[: match.start()].strip()
            right = line[match.end() :].strip()

            # Hai phía phải đủ dài mới coi là gutter giữa hai cột.
            if len(left) >= 20 and len(right) >= 20:
                return index

        return None

    @classmethod
    def _split_columns(cls, line: str) -> tuple[str, str] | None:
        """Tách một dòng thành cột trái và cột phải nếu có gutter rõ."""

        match = cls._COLUMN_GAP.search(line)

        if not match:
            return None

        left = line[: match.start()].strip()
        right = line[match.end() :].strip()

        if not left and not right:
            return None

        return left, right

    def raw_outline(self) -> list[Any]:
        """Cung cấp outline thô cho parser."""

        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")

        return list(self._reader.outline)

    def page_index_for_destination(self, destination: Any) -> int:
        """Lấy page index của một bookmark destination."""

        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")

        return self._reader.get_destination_page_number(destination)