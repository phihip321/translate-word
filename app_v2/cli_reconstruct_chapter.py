"""CLI kiểm tra tái cấu trúc text layer của một chapter, không AI/OCR."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.extractor import PdfTextExtractor
from app_v2.pdf.reconstructor import TextReconstructor
from app_v2.pdf.reader import PypdfReader


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Inspect reconstructed text segments for a chapter.")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("chapter_number", type=int)
    args = parser.parse_args(argv)

    reader = PypdfReader()
    document = reader.open(args.pdf_path)
    bookmarks = PypdfBookmarkParser().parse(reader)
    detected = OutlineChapterDetector().detect(bookmarks, document.page_count)
    if detected.needs_user_selection:
        print("No chapter group was selected with sufficient confidence.")
        return 2
    if not 1 <= args.chapter_number <= len(detected.chapters):
        parser.error(f"chapter_number must be between 1 and {len(detected.chapters)}")

    chapter = detected.chapters[args.chapter_number - 1]
    page_blocks = PdfTextExtractor().extract_chapter(reader, chapter)
    reconstructor = TextReconstructor()
    segments = reconstructor.reconstruct(page_blocks)
    report = reconstructor.audit(page_blocks, segments)

    print(f"CHAPTER {args.chapter_number}: {chapter.title}")
    print(f"Page blocks: {len(page_blocks)}")
    print(f"Segments: {len(segments)}")
    print(f"Source characters: {report.source_characters}")
    print(f"Reconstructed raw characters: {report.reconstructed_raw_characters}")
    print(f"Normalized characters: {report.normalized_characters}")
    print(f"Exact raw preservation: {'YES' if report.is_exactly_preserved else 'NO'}")
    print("Normalization: paragraph line breaks become spaces only in segment.text; raw_text is unchanged.")

    for segment in segments[:20]:
        pages = ", ".join(str(span.page_index + 1) for span in segment.source_spans)
        print()
        print(f"SEGMENT {segment.index}")
        print(f"Type: {segment.kind}")
        print(f"Source page(s): {pages}")
        print(f"Characters (normalized): {len(segment.text)}")
        print("Sample (first 300 characters):")
        print(segment.text[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
