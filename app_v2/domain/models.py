"""Mô hình dữ liệu độc lập với thư viện PDF hay AI cụ thể."""

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


def _readonly_metadata(values: Mapping[str, str] | None) -> Mapping[str, str]:
    return MappingProxyType(dict(values or {}))


@dataclass(frozen=True, slots=True)
class PdfDocument:
    """Thông tin tổng quan của một PDF, dùng chỉ số trang 0-based nội bộ."""

    path: Path
    page_count: int
    has_text_layer: bool
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_count < 0:
            raise ValueError("page_count không thể âm")
        object.__setattr__(self, "path", Path(self.path))
        object.__setattr__(self, "metadata", _readonly_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Bookmark:
    """Một mục outline PDF; ``level`` bắt đầu từ 0 và ``path`` giữ cây gốc."""

    title: str
    page_index: int
    level: int = 0
    path: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.page_index < 0 or self.level < 0:
            raise ValueError("page_index và level phải lớn hơn hoặc bằng 0")
        normalized_path = tuple(self.path) or (self.title,)
        if normalized_path[-1] != self.title:
            raise ValueError("path của bookmark phải kết thúc bằng title")
        object.__setattr__(self, "path", normalized_path)


@dataclass(frozen=True, slots=True)
class Chapter:
    """Phạm vi chương có cả trang đầu và trang cuối (0-based, inclusive)."""

    title: str
    start_page: int
    end_page: int
    bookmark: Bookmark | None = None

    def __post_init__(self) -> None:
        if self.start_page < 0 or self.end_page < self.start_page:
            raise ValueError("phạm vi trang chương không hợp lệ")


@dataclass(frozen=True, slots=True)
class ChapterCandidate:
    """Bookmark có dấu hiệu là chương nhưng chưa chắc được chọn."""

    bookmark: Bookmark
    reason: str


@dataclass(frozen=True, slots=True)
class ChapterDetectionResult:
    """Kết quả phát hiện, minh bạch khi cần người dùng quyết định."""

    chapters: tuple[Chapter, ...]
    candidates: tuple[ChapterCandidate, ...]
    selected_level: int | None
    needs_user_selection: bool


@dataclass(frozen=True, slots=True)
class TextBlock:
    """Text nguyên trạng từ text layer của một trang, không OCR."""

    text: str
    page_index: int
    block_index: int
    chapter: Chapter | None = None
    source_label: str = ""

    def __post_init__(self) -> None:
        if self.page_index < 0 or self.block_index < 0:
            raise ValueError("chỉ số trang và block không thể âm")


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Một khoảng ký tự nguyên trạng trong text layer của một trang PDF."""

    page_index: int
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if self.page_index < 0 or self.start_offset < 0 or self.end_offset < self.start_offset:
            raise ValueError("SourceSpan không hợp lệ")


@dataclass(frozen=True, slots=True)
class TextSegment:
    """Khối ổn định trước chunking, có text chuẩn hóa và bản nguồn chính xác."""

    index: int
    kind: str
    text: str
    raw_text: str
    source_spans: tuple[SourceSpan, ...]
    chapter: Chapter | None = None

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index TextSegment không thể âm")
        if not self.source_spans:
            raise ValueError("TextSegment cần ít nhất một SourceSpan")


@dataclass(frozen=True, slots=True)
class TextChunk:
    """Đơn vị dịch tương lai với metadata truy ngược về segment và PDF."""

    chunk_id: str
    chapter: Chapter | None
    sequence: int
    text: str
    segment_indices: tuple[int, ...]
    source_spans: tuple[SourceSpan, ...]
    char_count: int

    def __post_init__(self) -> None:
        if not self.chunk_id or self.sequence < 1 or not self.text:
            raise ValueError("TextChunk cần id, sequence dương và text không rỗng")
        if not self.segment_indices or not self.source_spans:
            raise ValueError("TextChunk cần segment_indices và source_spans")
        if self.char_count != len(self.text):
            raise ValueError("char_count phải bằng độ dài text")


@dataclass(frozen=True, slots=True)
class TranslatedChunk:
    """Kết quả dịch của một TextChunk, với mapping nguồn không thay đổi."""

    chunk_id: str
    chapter: Chapter | None
    sequence: int
    source_text: str
    translated_text: str
    source_segment_indices: tuple[int, ...]
    source_spans: tuple[SourceSpan, ...]
    provider: str
    model: str
    status: str

    def __post_init__(self) -> None:
        if not self.chunk_id or self.sequence < 1 or not self.source_text:
            raise ValueError("TranslatedChunk thiếu metadata nguồn cần thiết")
        if not self.source_segment_indices or not self.source_spans:
            raise ValueError("TranslatedChunk thiếu mapping nguồn")
        if not self.provider or not self.model or not self.status:
            raise ValueError("TranslatedChunk thiếu thông tin provider/model/status")
