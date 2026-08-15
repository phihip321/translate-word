"""Tạo các phạm vi chương từ danh sách bookmark đã chuẩn hóa."""

from collections.abc import Sequence

from app_v2.domain.models import Bookmark, Chapter


class BookmarkChapterManager:
    """Chọn bookmark ở một level làm chương và suy ra trang kết thúc."""

    def __init__(self, chapter_level: int = 0) -> None:
        if chapter_level < 0:
            raise ValueError("chapter_level không thể âm")
        self.chapter_level = chapter_level

    def build(self, bookmarks: Sequence[Bookmark], page_count: int) -> list[Chapter]:
        if page_count < 0:
            raise ValueError("page_count không thể âm")
        candidates = [b for b in bookmarks if b.level == self.chapter_level and b.page_index < page_count]
        chapters: list[Chapter] = []
        for index, bookmark in enumerate(candidates):
            next_start = candidates[index + 1].page_index if index + 1 < len(candidates) else page_count
            end_page = max(bookmark.page_index, next_start - 1)
            chapters.append(
                Chapter(
                    title=bookmark.title,
                    start_page=bookmark.page_index,
                    end_page=end_page,
                    bookmark=bookmark,
                )
            )
        return chapters
