"""Chia nội dung Chapter theo paragraph và gom thành batch."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app_v2.domain.models import Chapter, SourceSpan, TextSegment


# ============================================================
# CÁC MODEL CŨ - GIỮ LẠI ĐỂ CODE HIỆN TẠI KHÔNG BỊ HỎNG
# ============================================================

@dataclass(frozen=True, slots=True)
class ChunkingReport:
    """Báo cáo tương thích với hệ thống chunk cũ."""

    total_segments: int
    total_chunks: int
    total_characters: int


class SemanticTextChunker:
    """
    Compatibility wrapper.

    Code cũ vẫn có thể import SemanticTextChunker.
    Pipeline mới không sử dụng cách chia theo ký tự này.
    """

    def __init__(
        self,
        max_chars: int = 6000,
        **kwargs,
    ) -> None:
        self.max_chars = max_chars

    def chunk(
        self,
        chapter: Chapter,
        segments: Sequence[TextSegment],
    ):
        """
        Compatibility method.

        Pipeline dịch mới sử dụng ParagraphChunker bên dưới.
        """

        paragraphs, batches = ParagraphChunker(
            paragraphs_per_batch=10
        ).chunk(
            chapter,
            segments,
        )

        return paragraphs


# ============================================================
# PARAGRAPH
# ============================================================

@dataclass(frozen=True, slots=True)
class Paragraph:
    """Một paragraph độc lập - đơn vị cơ bản để dịch."""

    paragraph_id: str
    chapter: Chapter
    sequence: int
    text: str
    segment_indices: tuple[int, ...]
    source_spans: tuple[SourceSpan, ...]


# ============================================================
# TRANSLATION BATCH
# ============================================================

@dataclass(frozen=True, slots=True)
class TranslationBatch:
    """Một nhóm paragraph gửi cho Gemini."""

    batch_id: str
    chapter: Chapter
    sequence: int
    paragraphs: tuple[Paragraph, ...]


# ============================================================
# PARAGRAPH CHUNKER
# ============================================================

class ParagraphChunker:
    """
    Chia nội dung thành paragraph rồi gom thành batch.

    QUY TẮC:

    1 paragraph = 1 đơn vị dịch.

    Không chia paragraph theo số ký tự.

    Mặc định:

    10 paragraph = 1 batch.
    """

    def __init__(
        self,
        paragraphs_per_batch: int = 10,
    ) -> None:

        if paragraphs_per_batch <= 0:
            raise ValueError(
                "paragraphs_per_batch phải lớn hơn 0"
            )

        self.paragraphs_per_batch = paragraphs_per_batch

    # --------------------------------------------------------
    # PARAGRAPH
    # --------------------------------------------------------

    def extract_paragraphs(
        self,
        chapter: Chapter,
        segments: Sequence[TextSegment],
    ) -> list[Paragraph]:
        """
        Chuyển TextSegment thành paragraph.

        Không cắt paragraph theo ký tự.
        """

        paragraphs: list[Paragraph] = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            # Chỉ lấy paragraph.
            if segment.kind != "paragraph":
                continue

            sequence = len(paragraphs) + 1

            paragraphs.append(
                Paragraph(
                    paragraph_id=f"P{sequence:06d}",
                    chapter=chapter,
                    sequence=sequence,
                    text=text,
                    segment_indices=(segment.index,),
                    source_spans=tuple(
                        segment.source_spans
                    ),
                )
            )

        return paragraphs

    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------

    def create_batches(
        self,
        chapter: Chapter,
        paragraphs: Sequence[Paragraph],
    ) -> list[TranslationBatch]:

        batches: list[TranslationBatch] = []

        for start in range(
            0,
            len(paragraphs),
            self.paragraphs_per_batch,
        ):

            batch_paragraphs = tuple(
                paragraphs[
                    start:
                    start + self.paragraphs_per_batch
                ]
            )

            sequence = len(batches) + 1

            batches.append(
                TranslationBatch(
                    batch_id=f"B{sequence:06d}",
                    chapter=chapter,
                    sequence=sequence,
                    paragraphs=batch_paragraphs,
                )
            )

        return batches

    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    def chunk(
        self,
        chapter: Chapter,
        segments: Sequence[TextSegment],
    ) -> tuple[
        list[Paragraph],
        list[TranslationBatch],
    ]:

        paragraphs = self.extract_paragraphs(
            chapter,
            segments,
        )

        batches = self.create_batches(
            chapter,
            paragraphs,
        )

        return paragraphs, batches