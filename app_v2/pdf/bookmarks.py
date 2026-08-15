"""Chuyển outline PDF thành bookmark miền, chưa gắn với GUI."""

from typing import Any

from app_v2.domain.models import Bookmark
from .reader import PypdfReader


class PypdfBookmarkParser:
    """Duyệt outline lồng nhau của pypdf thành danh sách theo thứ tự đọc."""

    def parse(self, reader: PypdfReader) -> list[Bookmark]:
        bookmarks: list[Bookmark] = []

        def walk(items: list[Any], level: int, ancestors: tuple[str, ...]) -> None:
            previous_title: str | None = None
            for item in items:
                if isinstance(item, list):
                    child_ancestors = ancestors + ((previous_title,) if previous_title else ())
                    walk(item, level + 1, child_ancestors)
                    continue
                try:
                    page_index = reader.page_index_for_destination(item)
                except (KeyError, TypeError, ValueError):
                    continue
                title = str(getattr(item, "title", "") or "Untitled bookmark").strip()
                bookmarks.append(
                    Bookmark(
                        title=title,
                        page_index=page_index,
                        level=level,
                        path=ancestors + (title,),
                    )
                )
                previous_title = title

        walk(reader.raw_outline(), level=0, ancestors=())
        return bookmarks
