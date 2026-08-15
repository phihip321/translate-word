"""Nhận diện chapter chỉ từ cấu trúc outline PDF."""

from collections import defaultdict
from collections.abc import Sequence
import re

from app_v2.domain.models import (
    Bookmark,
    Chapter,
    ChapterCandidate,
    ChapterDetectionResult,
)


class OutlineChapterDetector:
    """Chọn chapter khi bookmark cung cấp bằng chứng cấu trúc đủ mạnh.

    Tiêu đề ``Chapter 1``/``Ch. 1`` là bằng chứng trực tiếp. Tiêu đề đánh số
    dạng ``1: ...`` chỉ được chọn tự động khi tạo một dãy liên tiếp bắt đầu từ
    1, ở cùng một cấp outline. Các trường hợp khác được trả về như candidate.
    """

    _excluded = re.compile(
        r"^\s*(part\b|dedication\b|foreword\b|preface\b|"
        r"acknowledg(?:e)?ments?\b|contents?\b|contributors?\b|index\b)",
        re.IGNORECASE,
    )
    _chapter_word = re.compile(r"\b(?:chapter\s+|ch\.\s*)\d+\b", re.IGNORECASE)
    _numbered = re.compile(r"^\s*(\d+)\s*(?::|\.|-)\s*\S")

    def detect(
        self, bookmarks: Sequence[Bookmark], page_count: int
    ) -> ChapterDetectionResult:
        if page_count < 0:
            raise ValueError("page_count không thể âm")

        candidates: list[ChapterCandidate] = []
        direct_by_level: dict[int, list[Bookmark]] = defaultdict(list)
        numbered_by_level: dict[int, list[tuple[int, Bookmark]]] = defaultdict(list)

        for bookmark in bookmarks:
            if bookmark.page_index >= page_count or self._excluded.match(bookmark.title):
                continue
            if self._chapter_word.match(bookmark.title):
                direct_by_level[bookmark.level].append(bookmark)
                candidates.append(ChapterCandidate(bookmark, "title contains Chapter/Ch. with a number"))
                continue
            match = self._numbered.match(bookmark.title)
            if match:
                number = int(match.group(1))
                numbered_by_level[bookmark.level].append((number, bookmark))
                candidates.append(ChapterCandidate(bookmark, "numbered bookmark title"))

        selected_level, selected = self._select_direct_group(direct_by_level)
        if not selected:
            selected_level, selected = self._select_numbered_sequence(numbered_by_level)

        if not selected:
            return ChapterDetectionResult(
                chapters=(),
                candidates=tuple(candidates),
                selected_level=None,
                needs_user_selection=bool(candidates),
            )

        chapters = self._build_ranges(bookmarks, selected, page_count)
        return ChapterDetectionResult(
            chapters=tuple(chapters),
            candidates=tuple(candidates),
            selected_level=selected_level,
            needs_user_selection=False,
        )

    @staticmethod
    def _select_direct_group(groups: dict[int, list[Bookmark]]) -> tuple[int | None, list[Bookmark]]:
        eligible = [(level, items) for level, items in groups.items() if len(items) >= 2]
        if not eligible:
            return None, []
        level, items = max(eligible, key=lambda group: len(group[1]))
        return level, items

    @staticmethod
    def _select_numbered_sequence(
        groups: dict[int, list[tuple[int, Bookmark]]]
    ) -> tuple[int | None, list[Bookmark]]:
        valid: list[tuple[int, list[Bookmark]]] = []
        for level, numbered in groups.items():
            numbers = [number for number, _ in numbered]
            if len(numbers) >= 2 and numbers == list(range(1, len(numbers) + 1)):
                valid.append((level, [bookmark for _, bookmark in numbered]))
        if not valid:
            return None, []
        level, bookmarks = max(valid, key=lambda group: len(group[1]))
        return level, bookmarks

    @staticmethod
    def _build_ranges(
        all_bookmarks: Sequence[Bookmark], selected: Sequence[Bookmark], page_count: int
    ) -> list[Chapter]:
        positions = {id(bookmark): index for index, bookmark in enumerate(all_bookmarks)}
        selected_by_parent: dict[tuple[str, ...], list[Bookmark]] = defaultdict(list)
        for bookmark in selected:
            selected_by_parent[bookmark.path[:-1]].append(bookmark)

        chapters: list[Chapter] = []
        for bookmark in selected:
            siblings = selected_by_parent[bookmark.path[:-1]]
            sibling_position = siblings.index(bookmark)
            if sibling_position + 1 < len(siblings):
                end_page = siblings[sibling_position + 1].page_index - 1
            else:
                end_page = OutlineChapterDetector._parent_end_page(
                    all_bookmarks, positions[id(bookmark)], bookmark, page_count
                )
            chapters.append(
                Chapter(
                    title=bookmark.title,
                    start_page=bookmark.page_index,
                    end_page=max(bookmark.page_index, end_page),
                    bookmark=bookmark,
                )
            )
        return chapters

    @staticmethod
    def _parent_end_page(
        bookmarks: Sequence[Bookmark], current_index: int, bookmark: Bookmark, page_count: int
    ) -> int:
        parent_level = bookmark.level - 1
        if parent_level < 0:
            return page_count - 1
        for later in bookmarks[current_index + 1 :]:
            if later.level <= parent_level:
                return later.page_index - 1
        return page_count - 1
