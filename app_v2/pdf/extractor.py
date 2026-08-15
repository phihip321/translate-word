"""Trích text layer từ phạm vi trang; cố ý không OCR."""

from app_v2.domain.contracts import PdfReaderContract
from app_v2.domain.models import Chapter, TextBlock


class PdfTextExtractor:
    """Tạo đúng một TextBlock cho mỗi trang trong phạm vi, kể cả trang rỗng."""

    def extract_chapter(self, reader: PdfReaderContract, chapter: Chapter) -> list[TextBlock]:
        return self.extract_pages(
            reader, chapter.start_page, chapter.end_page, chapter=chapter
        )

    def extract_pages(
        self,
        reader: PdfReaderContract,
        start_page: int,
        end_page: int,
        *,
        chapter: Chapter | None = None,
    ) -> list[TextBlock]:
        if start_page < 0 or end_page < start_page:
            raise ValueError("phạm vi trang không hợp lệ")
        blocks: list[TextBlock] = []
        for page_index in range(start_page, end_page + 1):
            text = reader.extract_page_text(page_index)
            blocks.append(
                TextBlock(
                    text=text,
                    page_index=page_index,
                    block_index=len(blocks),
                    chapter=chapter,
                )
            )
        return blocks
