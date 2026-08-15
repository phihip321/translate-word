"""Khung chia text tuần tự; chưa thực hiện tối ưu theo token."""

from collections.abc import Sequence

from app_v2.domain.models import SourceSpan, TextBlock, TextChunk


class CharacterTextSplitter:
    """Gom block theo số ký tự để chuẩn bị cho translator ở giai đoạn sau."""

    def __init__(self, max_characters: int = 6_000) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters phải lớn hơn 0")
        self.max_characters = max_characters

    def split(self, blocks: Sequence[TextBlock]) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        current: list[TextBlock] = []
        current_length = 0

        def flush() -> None:
            nonlocal current, current_length
            if not current:
                return
            chunks.append(
                TextChunk(
                    chunk_id=f"legacy-block-{len(chunks) + 1:03d}",
                    chapter=current[0].chapter,
                    sequence=len(chunks) + 1,
                    text="\n\n".join(block.text for block in current),
                    segment_indices=tuple(block.block_index for block in current),
                    source_spans=tuple(
                        SourceSpan(block.page_index, 0, len(block.text)) for block in current
                    ),
                    char_count=len("\n\n".join(block.text for block in current)),
                )
            )
            current, current_length = [], 0

        for block in blocks:
            added_length = len(block.text) + (2 if current else 0)
            if current and current_length + added_length > self.max_characters:
                flush()
            current.append(block)
            current_length += added_length
        flush()
        return chunks
