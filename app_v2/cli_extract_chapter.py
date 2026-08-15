"""CLI kiểm tra text layer của một chapter, không OCR hoặc dịch."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.extractor import PdfTextExtractor
from app_v2.pdf.reader import PypdfReader


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Inspect text extraction for one detected chapter.")
    parser.add_argument("pdf_path", type=Path, help="Path to the PDF file")
    parser.add_argument("chapter_number", type=int, help="One-based detected chapter number")
    args = parser.parse_args(argv)

    reader = PypdfReader()
    document = reader.open(args.pdf_path)
    bookmarks = PypdfBookmarkParser().parse(reader)
    result = OutlineChapterDetector().detect(bookmarks, document.page_count)
    if result.needs_user_selection:
        print("No chapter group was selected with sufficient confidence.")
        return 2
    if not 1 <= args.chapter_number <= len(result.chapters):
        parser.error(f"chapter_number must be between 1 and {len(result.chapters)}")

    chapter = result.chapters[args.chapter_number - 1]
    pages = PdfTextExtractor().extract_chapter(reader, chapter)
    expected_pages = chapter.end_page - chapter.start_page + 1

    print(f"CHAPTER {args.chapter_number}")
    print(f"Title: {chapter.title}")
    print(f"Start page: {chapter.start_page + 1}")
    print(f"End page: {chapter.end_page + 1}")
    print(f"Expected pages: {expected_pages}")
    print(f"Extracted pages: {len(pages)}")

    for block in pages:
        print()
        print(f"PAGE {block.page_index + 1}")
        print(f"Characters: {len(block.text)}")
        if not block.text:
            print("Text status: EMPTY")
            continue
        print("Sample (first 500 characters):")
        print(block.text[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
