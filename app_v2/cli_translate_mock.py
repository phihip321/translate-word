"""CLI kiểm tra pipeline tới MockTranslator; không gửi dữ liệu ra Internet."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app_v2.config.settings import ProviderSettings
from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.chunker import SemanticTextChunker
from app_v2.pdf.extractor import PdfTextExtractor
from app_v2.pdf.reconstructor import TextReconstructor
from app_v2.pdf.reader import PypdfReader
from app_v2.services.translation_manager import TranslationManager
from app_v2.translators.factory import create_translator


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Run the local mock translation pipeline for one chapter.")
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
    chunks = SemanticTextChunker().chunk(chapter, segments)
    translator = create_translator(ProviderSettings(provider="mock"))
    translated = TranslationManager(translator).translate(chunks)

    print(f"Chapter: {args.chapter_number}")
    print(f"Chunks: {len(chunks)}")
    print(f"Translated chunks: {len(translated)}")
    print(f"Provider: {translator.provider}")
    print(f"Model: {translator.model}")
    print(f"Source preserved: {'YES' if all(item.source_text == chunk.text for chunk, item in zip(chunks, translated, strict=True)) else 'NO'}")
    for item in translated:
        print(f"- {item.chunk_id} | sequence={item.sequence} | chars={len(item.source_text)} | status={item.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
