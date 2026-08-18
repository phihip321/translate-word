import tkinter as tk
from tkinter import filedialog
import pymupdf
import re


def choose_pdf():
    """Mở hộp thoại chọn file PDF."""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Chọn sách PDF",
        filetypes=[("PDF files", "*.pdf")]
    )

    root.destroy()
    return file_path


def find_chapters(pdf_path):
    """
    Tìm Chapter dựa trên Bookmark Level 2.

    Điều kiện:
    - Bookmark phải ở Level 2
    - Tên phải bắt đầu bằng số + dấu :
      Ví dụ:
          1: Imaging in Interventional Pain Management
          2: Basics of Ultrasound
    """

    doc = pymupdf.open(pdf_path)
    toc = doc.get_toc()

    chapters = []

    for level, title, page in toc:

        # Chỉ lấy Bookmark Level 2
        if level != 2:
            continue

        title = title.strip()

        # Kiểm tra dạng:
        # 1: ...
        # 2: ...
        # 36: ...
        match = re.match(r"^(\d+)\s*:\s*(.+)$", title)

        if not match:
            continue

        chapter_number = int(match.group(1))
        chapter_title = match.group(2).strip()

        chapters.append({
            "number": chapter_number,
            "title": chapter_title,
            "start": page,
        })

    # Tính trang kết thúc
    for i in range(len(chapters)):

        if i < len(chapters) - 1:
            chapters[i]["end"] = chapters[i + 1]["start"] - 1

        else:
            # Chapter cuối:
            # kết thúc trước Index.
            # Nếu có Index ở Level 1 thì dùng trang Index - 1.
            index_page = None

            for level, title, page in toc:
                if level == 1 and title.strip().lower() == "index":
                    index_page = page
                    break

            if index_page is not None:
                chapters[i]["end"] = index_page - 1
            else:
                chapters[i]["end"] = len(doc)

    doc.close()

    return chapters


def main():

    print("=" * 80)
    print("TÌM CHAPTER TỪ BOOKMARK PDF")
    print("=" * 80)

    pdf_path = choose_pdf()

    if not pdf_path:
        print("Bạn chưa chọn file PDF.")
        return

    print()
    print(f"File: {pdf_path}")

    print()
    print("Đang đọc Bookmark...")

    try:
        chapters = find_chapters(pdf_path)

    except Exception as e:
        print()
        print("LỖI:")
        print(e)
        return

    print()
    print("=" * 80)
    print("DANH SÁCH CHAPTER")
    print("=" * 80)

    if not chapters:
        print("Không tìm thấy Chapter.")
        return

    for chapter in chapters:
        print(
            f"Chapter {chapter['number']}: "
            f"{chapter['title']}"
        )

        print(
            f"    Trang {chapter['start']} → "
            f"{chapter['end']}"
        )

    print()
    print("=" * 80)
    print(f"TỔNG SỐ CHAPTER: {len(chapters)}")
    print("=" * 80)


if __name__ == "__main__":
    main()