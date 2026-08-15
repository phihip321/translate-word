"""Gửi duy nhất một câu test ngắn tới Gemini; không đọc PDF."""

from __future__ import annotations

from dotenv import load_dotenv

from app_v2.config.settings import ProviderSettings
from app_v2.domain.models import Chapter, SourceSpan, TextChunk
from app_v2.services.translation_manager import TranslationManager
from app_v2.translators.factory import create_translator


def main() -> int:
    # Nạp .env vào environment; GeminiTranslator chỉ đọc os.getenv("GEMINI_API_KEY").
    load_dotenv()
    settings = ProviderSettings(provider="gemini")
    chunk = TextChunk(
        chunk_id="gemini-short-test-001",
        chapter=Chapter("Gemini short test", 0, 0),
        sequence=1,
        text="Ultrasound examination revealed a small joint effusion.",
        segment_indices=(0,),
        source_spans=(SourceSpan(page_index=0, start_offset=0, end_offset=55),),
        char_count=55,
    )
    translator = create_translator(settings)
    translated = TranslationManager(translator).translate([chunk])[0]
    print(f"Provider: {translated.provider}")
    print(f"Model: {translated.model}")
    print(f"Source: {translated.source_text}")
    print(f"Translation: {translated.translated_text}")
    print(f"Status: {translated.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
