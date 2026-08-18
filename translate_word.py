import tkinter as tk
from tkinter import filedialog
import fitz  # PyMuPDF


def choose_pdf():
    """Mở hộp thoại để chọn file PDF."""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Chọn sách PDF",
        filetypes=[("PDF files", "*.pdf")]
    )

    root.destroy()
    return file_path


def get_chapters(pdf_path):
    """
    Đọc Bookmark/Outline của PDF.
    Trả về danh sách:
        {
            "title": tên chương,
            "start": trang bắt đầu,
            "end": trang kết thúc
        }
    """

    doc = fitz.open(pdf_path)

    # Lấy toàn bộ bookmark
    toc = doc.get_toc()

    chapters = []

    for item in toc:
        level, title, page = item

        # Chỉ lấy các mục cấp 1
        # Ví dụ:
        # 1 Chapter 1
        # 2 Chapter 2
        if level == 1:
            chapters.append({
                "title": title.strip(),
                "start": page
            })

    # Tính trang kết thúc
    for i in range(len(chapters)):
        if i < len(chapters) - 1:
            chapters[i]["end"] = chapters[i + 1]["start"] - 1
        else:
            chapters[i]["end"] = len(doc)

    doc.close()

    return chapters


def main():

    print("=" * 70)
    print("KIỂM TRA CHAPTER TỪ BOOKMARK PDF")
    print("=" * 70)

    pdf_path = choose_pdf()

    if not pdf_path:
        print("Bạn chưa chọn file PDF.")
        return

    print()
    print("File đã chọn:")
    print(pdf_path)

    print()
    print("Đang đọc Bookmark...")

    try:
        chapters = get_chapters(pdf_path)
    except Exception as e:
        print()
        print("LỖI:")
        print(e)
        return

    print()
    print("=" * 70)
    print("KẾT QUẢ")
    print("=" * 70)

    if not chapters:
        print("Không tìm thấy Chapter cấp 1 trong Bookmark.")
        return

    for i, chapter in enumerate(chapters, start=1):
        print(
            f"{i:3}. {chapter['title']}"
        )
        print(
            f"     Trang: {chapter['start']} → {chapter['end']}"
        )

    print()
    print(f"Tổng số Chapter tìm được: {len(chapters)}")


if __name__ == "__main__":
    main()