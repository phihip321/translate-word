"""Các protocol tách logic V2 khỏi implementation của thư viện PDF."""

from pathlib import Path
from typing import Protocol, Sequence

from .models import Bookmark, Chapter, PdfDocument, TextBlock, TextChunk, TextSegment, TranslatedChunk


class PdfReaderContract(Protocol):
    def open(self, path: Path) -> PdfDocument: ...
    def extract_page_text(self, page_index: int) -> str: ...


class BookmarkParserContract(Protocol):
    def parse(self, reader: PdfReaderContract) -> Sequence[Bookmark]: ...


class ChapterManagerContract(Protocol):
    def build(self, bookmarks: Sequence[Bookmark], page_count: int) -> Sequence[Chapter]: ...


class TextExtractorContract(Protocol):
    def extract_pages(
        self, reader: PdfReaderContract, start_page: int, end_page: int
    ) -> Sequence[TextBlock]: ...


class TextSplitterContract(Protocol):
    def split(self, blocks: Sequence[TextBlock]) -> Sequence[TextChunk]: ...


class TextReconstructorContract(Protocol):
    def reconstruct(self, page_blocks: Sequence[TextBlock]) -> Sequence[TextSegment]: ...


class TextChunkerContract(Protocol):
    def chunk(self, chapter: Chapter, segments: Sequence[TextSegment]) -> Sequence[TextChunk]: ...


class AITranslatorContract(Protocol):
    provider: str
    model: str

    def translate(self, chunk: TextChunk) -> TranslatedChunk: ...
