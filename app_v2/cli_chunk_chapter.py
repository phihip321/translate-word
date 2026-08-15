"""CLI kiểm tra semantic chunking của một chapter, không AI/OCR."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.chunker import SemanticTextChunker
from app_v2.pdf.extractor import PdfTextExtractor
from app_v2.pdf.reconstructor import TextReconstructor
from app_v2.pdf.reader import PypdfReader


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Inspect semantic chunks for a detected chapter.")
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
    segments = TextReconstructor().reconstruct(PdfTextExtractor().extract_chapter(reader, chapter))
    chunker = SemanticTextChunker()
    chunks = chunker.chunk(chapter, segments)
    report = chunker.audit(segments, chunks)

    print(f"Chapter: {args.chapter_number}")
    print(f"Segments: {len(segments)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Input chars: {report.input_characters}")
    print(f"Chunk chars: {report.chunk_characters}")
    print(f"Exact normalized preservation: {'YES' if report.is_exactly_preserved else 'NO'}")
    for chunk in chunks:
        pages = ", ".join(str(span.page_index + 1) for span in chunk.source_spans)
        indices = ", ".join(str(index) for index in chunk.segment_indices)
        print()
        print(f"Chunk {chunk.sequence:03d}")
        print(f"- chars: {chunk.char_count}")
        print(f"- segments: {indices}")
        print(f"- pages: {pages}")
        print("- first 300 chars:")
        print(chunk.text[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
