"""Các mô hình và hợp đồng miền cho V2."""

from .models import (
    Bookmark,
    Chapter,
    ChapterCandidate,
    ChapterDetectionResult,
    PdfDocument,
    SourceSpan,
    TextBlock,
    TextChunk,
    TextSegment,
    TranslatedChunk,
)

__all__ = [
    "Bookmark",
    "Chapter",
    "ChapterCandidate",
    "ChapterDetectionResult",
    "PdfDocument",
    "SourceSpan",
    "TextBlock",
    "TextChunk",
    "TextSegment",
    "TranslatedChunk",
]
