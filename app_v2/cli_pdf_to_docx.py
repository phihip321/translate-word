"""CLI chuyển PDF → DOCX sạch kiểu "Formatted Text" (chưa ảnh/caption/bảng/dịch)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.docx.writer import DocxWriter
from app_v2.domain.models import Chapter
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

    parser = argparse.ArgumentParser(
        description="Convert a PDF to a clean structured DOCX (text only)."
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the input PDF file")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output .docx path (default: <pdf_name>.docx next to the PDF)",
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Only convert this one-based detected chapter (default: all chapters)",
    )
    args = parser.parse_args(argv)

    reader = PypdfReader()
    document = reader.open(args.pdf_path)
    bookmarks = PypdfBookmarkParser().parse(reader)
    detected = OutlineChapterDetector().detect(bookmarks, document.page_count)

    if args.chapter is not None:
        if detected.needs_user_selection or not detected.chapters:
            parser.error("No chapters detected; cannot use --chapter.")
        if not 1 <= args.chapter <= len(detected.chapters):
            parser.error(f"chapter must be between 1 and {len(detected.chapters)}")
        chapters = [detected.chapters[args.chapter - 1]]
    elif detected.chapters and not detected.needs_user_selection:
        chapters = list(detected.chapters)
    else:
        # Không có chapter detection → chuyển toàn bộ PDF như một chapter duy nhất.
        chapters = [
            Chapter(
                title=args.pdf_path.stem,
                start_page=0,
                end_page=document.page_count - 1,
            )
        ]

    output_path = args.output or args.pdf_path.with_suffix(".docx")
    writer = DocxWriter()
    total_segments = 0

    for chapter in chapters:
        page_blocks = PdfTextExtractor().extract_chapter(reader, chapter)
        segments = TextReconstructor().reconstruct(page_blocks)
        writer.write_segments(segments)
        total_segments += len(segments)

    writer.save(str(output_path))

    print(f"PDF: {args.pdf_path}")
    print(f"Chapters converted: {len(chapters)}")
    print(f"Total segments written: {total_segments}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())