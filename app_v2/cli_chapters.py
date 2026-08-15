"""CLI kiểm tra phát hiện chapter từ PDF outline, không dịch nội dung."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.reader import PypdfReader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect chapters from a PDF outline only.")
    parser.add_argument("pdf_path", type=Path, help="Path to the PDF file")
    args = parser.parse_args(argv)

    reader = PypdfReader()
    document = reader.open(args.pdf_path)
    bookmarks = PypdfBookmarkParser().parse(reader)
    result = OutlineChapterDetector().detect(bookmarks, document.page_count)

    if result.needs_user_selection:
        print("No chapter group was selected with sufficient confidence.")
        print("Candidates for user selection:")
        for candidate in result.candidates:
            bookmark = candidate.bookmark
            print(f"- {bookmark.title} | level {bookmark.level} | page {bookmark.page_index + 1}")
        return 2

    print(f"Detected {len(result.chapters)} chapters at bookmark level {result.selected_level}.")
    for index, chapter in enumerate(result.chapters, start=1):
        bookmark = chapter.bookmark
        assert bookmark is not None
        print()
        print(f"CHAPTER {index}")
        print(f"Title: {chapter.title}")
        print(f"Path: {' > '.join(bookmark.path)}")
        print(f"Bookmark level: {bookmark.level}")
        print(f"Start page: {chapter.start_page + 1}")
        print(f"End page: {chapter.end_page + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
