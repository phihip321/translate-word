"""Adapter đọc PDF dự kiến dùng pypdf.

``pypdf`` được chọn vì hỗ trợ metadata, trích text và outline PDF. Dependency
được import trễ để Giai đoạn 1 vẫn chạy khi package này chưa được cài.
"""

from pathlib import Path
from typing import Any

from app_v2.domain.models import PdfDocument


class PdfDependencyError(RuntimeError):
    """Báo rõ dependency PDF cần được bổ sung trước khi đọc file."""


class PypdfReader:
    """Adapter stateful bao quanh ``pypdf.PdfReader`` sau khi mở một file."""

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
        has_text_layer = any(self.extract_page_text(i).strip() for i in range(len(self._reader.pages)))
        self._document = PdfDocument(
            path=pdf_path,
            page_count=len(self._reader.pages),
            has_text_layer=has_text_layer,
            metadata=metadata,
        )
        return self._document

    def extract_page_text(self, page_index: int) -> str:
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        if not 0 <= page_index < len(self._reader.pages):
            raise IndexError(f"Trang không hợp lệ: {page_index}")
        return self._reader.pages[page_index].extract_text() or ""

    def raw_outline(self) -> list[Any]:
        """Cung cấp outline thô cho parser mà không lộ ra ngoài domain."""
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        return list(self._reader.outline)

    def page_index_for_destination(self, destination: Any) -> int:
        if self._reader is None:
            raise RuntimeError("Chưa mở PDF")
        return self._reader.get_destination_page_number(destination)
