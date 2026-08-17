from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from app_v2.pdf.reader import PypdfReader
from app_v2.pdf.bookmarks import PypdfBookmarkParser
from app_v2.pdf.chapter_detection import OutlineChapterDetector
from app_v2.pdf.extractor import PdfTextExtractor
from app_v2.pdf.reconstructor import TextReconstructor
from app_v2.pdf.chunker import ParagraphChunker


def choose_pdf() -> Path | None:
    """Hiện cửa sổ để người dùng chọn file PDF."""

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Chọn file PDF",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()

    if not file_path:
        return None

    return Path(file_path)


def main():
    print("=" * 70)
    print("KIỂM TRA PARAGRAPH → BATCH")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. Chọn PDF
    # ---------------------------------------------------------

    pdf_path = choose_pdf()

    if pdf_path is None:
        print("Bạn chưa chọn file PDF.")
        return 1

    print(f"Đã chọn: {pdf_path}")
    print()

    # ---------------------------------------------------------
    # 2. Đọc PDF
    # ---------------------------------------------------------

    reader = PypdfReader()
    document = reader.open(pdf_path)

    print(f"Số trang PDF: {document.page_count}")

    # ---------------------------------------------------------
    # 3. Đọc bookmark
    # ---------------------------------------------------------

    bookmarks = PypdfBookmarkParser().parse(reader)

    # ---------------------------------------------------------
    # 4. Tìm Chapter
    # ---------------------------------------------------------

    detector = OutlineChapterDetector()

    result = detector.detect(
        bookmarks,
        document.page_count,
    )

    if not result.chapters:
        print()
        print("Không tìm thấy Chapter.")
        return 1

    print()
    print("Các Chapter tìm được:")
    print()

    for i, chapter in enumerate(
        result.chapters,
        start=1,
    ):
        print(
            f"{i}. {chapter.title} "
            f"(trang {chapter.start_page + 1}"
            f"-{chapter.end_page + 1})"
        )

    # ---------------------------------------------------------
    # 5. Tạm thời lấy Chapter đầu tiên
    # ---------------------------------------------------------

    chapter = result.chapters[0]

    print()
    print("=" * 70)
    print(f"ĐANG KIỂM TRA: {chapter.title}")
    print("=" * 70)

    # ---------------------------------------------------------
    # 6. Extract text
    # ---------------------------------------------------------

    extractor = PdfTextExtractor()

    page_blocks = extractor.extract_chapter(
        reader,
        chapter,
    )

    print(
        f"Số page block: {len(page_blocks)}"
    )

    # ---------------------------------------------------------
    # 7. Reconstruct
    # ---------------------------------------------------------

    reconstructor = TextReconstructor()

    segments = reconstructor.reconstruct(
        page_blocks
    )

    print(
        f"Số TextSegment: {len(segments)}"
    )

    # ---------------------------------------------------------
    # 8. Paragraph → Batch
    # ---------------------------------------------------------

    chunker = ParagraphChunker(
        paragraphs_per_batch=10
    )

    paragraphs, batches = chunker.chunk(
        chapter,
        segments,
    )

    # ---------------------------------------------------------
    # 9. Kết quả
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("KẾT QUẢ")
    print("=" * 70)

    print()
    print(
        f"Tổng paragraph: {len(paragraphs)}"
    )

    print(
        f"Tổng batch:     {len(batches)}"
    )

    print()

    # ---------------------------------------------------------
    # 10. Hiển thị batch
    # ---------------------------------------------------------

    for batch in batches:

        print("=" * 70)

        print(
            f"{batch.batch_id} "
            f"→ {len(batch.paragraphs)} paragraph"
        )

        print("=" * 70)

        for paragraph in batch.paragraphs:

            preview = paragraph.text.replace(
                "\n",
                " ",
            )

            if len(preview) > 150:
                preview = preview[:150] + "..."

            print(
                f"[{paragraph.paragraph_id}] "
                f"{preview}"
            )

        print()

    print("=" * 70)
    print("HOÀN THÀNH KIỂM TRA")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())