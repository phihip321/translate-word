"""
Ứng dụng dịch sách - Hỗ trợ ảnh và bảng
"""
import os
import yaml
import logging
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tkinter import Tk, filedialog

from pdf_processor import PDFProcessor
from translator import GeminiTranslator
from docx_generator import DOCXGenerator

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BookTranslator:
    def __init__(self):
        self.model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')
        self.pdf_processor = PDFProcessor()
        self.translator = GeminiTranslator(model=self.model)
        
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.docx_generator = DOCXGenerator(self.config['docx'])
        self.current_pdf = None
        self.current_chapters = {}
        self.selected_chapter = None
        self.images = []
    
    def select_pdf_gui(self):
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF cần dịch",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=os.path.expanduser("~\\Desktop")
        )
        root.destroy()
        if not file_path:
            return False
        self.current_pdf = file_path
        print(f"✅ Đã chọn: {os.path.basename(file_path)}")
        return True
    
    def select_pdf(self):
        print("\n" + "=" * 60)
        print("📚 ỨNG DỤNG DỊCH SÁCH TỰ ĐỘNG")
        print("=" * 60)
        try:
            return self.select_pdf_gui()
        except:
            pdf_path = input("📄 Nhập đường dẫn PDF: ").strip()
            if os.path.exists(pdf_path):
                self.current_pdf = pdf_path
                return True
            return False
    
    def extract_chapters_only(self):
        """
        BƯỚC 1: CHỈ LẤY DANH SÁCH CHAPTER (KHÔNG TRÍCH XUẤT ẢNH)
        """
        print("\n📑 Đang đọc Bookmark (mục lục)...")
        
        # Set path cho pdf_processor
        self.pdf_processor.pdf_path = self.current_pdf
        
        # Lấy bookmark
        bookmarks = self.pdf_processor.get_bookmarks()
        
        if bookmarks:
            print(f"📚 Tìm thấy {len(bookmarks)} bookmark")
            
            # Trích xuất chapter từ bookmark
            chapters = {}
            for bm in bookmarks:
                title = bm["title"].strip()
                
                # Tìm Chapter trong bookmark
                match = re.search(r'(?i)^(?:chapter|chương)\s+(\d+|[IVXLCDM]+)\s*[:.]?\s*(.*?)$', title)
                
                if match:
                    chapter_num = match.group(1)
                    chapter_title = match.group(2).strip()
                    
                    if chapter_title:
                        chapter_name = f"Chapter {chapter_num}: {chapter_title}"
                    else:
                        chapter_name = f"Chapter {chapter_num}"
                    
                    chapters[chapter_name] = ""
            
            # Nếu tìm thấy chapter
            if chapters:
                self.current_chapters = chapters
                self._show_chapters()
                return True
        
        # Fallback: Không có bookmark, thử detect từ text
        print("📑 Không có Bookmark, đọc text để tìm chapter...")
        text = self.pdf_processor.extract_text(self.current_pdf)
        if text:
            self.current_chapters = self.pdf_processor._detect_from_headings(text)
            self._show_chapters()
            return True
        
        print("❌ Không thể tìm thấy chapter")
        return False
    
    def _show_chapters(self):
        """Hiển thị danh sách chapter và cho chọn"""
        chapter_list = list(self.current_chapters.keys())
        
        print(f"\n📚 TÌM THẤY {len(chapter_list)} CHAPTER:")
        print("-" * 60)
        for i, ch in enumerate(chapter_list, 1):
            print(f"  {i}. {ch}")
        print("-" * 60)
        
        choice = input(f"\n👉 Chọn chapter (1-{len(chapter_list)}) hoặc 'all': ").strip()
        
        if choice.lower() == 'all':
            self.selected_chapter = "ALL"
            print("✅ Sẽ dịch tất cả chapter")
        elif choice.isdigit() and 1 <= int(choice) <= len(chapter_list):
            self.selected_chapter = chapter_list[int(choice) - 1]
            print(f"✅ Đã chọn: {self.selected_chapter}")
        else:
            print("❌ Lựa chọn không hợp lệ")
    
    def extract_images_and_content(self):
        """
        BƯỚC 2: TRÍCH XUẤT ẢNH VÀ NỘI DUNG CHAPTER ĐÃ CHỌN
        """
        print("\n📖 Đang trích xuất ảnh và nội dung...")
        
        # Trích xuất toàn bộ text và ảnh
        text, self.images = self.pdf_processor.extract_text_and_images(self.current_pdf)
        
        if not text:
            print("❌ Không thể trích xuất văn bản")
            return False
        
        print(f"✅ Trích xuất {len(self.images)} ảnh")
        
        # Lấy nội dung chapter đã chọn
        if self.selected_chapter != "ALL":
            # Tìm nội dung chapter trong text
            content = self._get_chapter_content(text)
            if content:
                self.current_chapters[self.selected_chapter] = content
                print(f"✅ Lấy được nội dung chapter: {len(content)} ký tự")
            else:
                print("⚠️ Không tìm thấy nội dung chapter, sẽ dịch toàn bộ")
        
        return True
    
    def _get_chapter_content(self, full_text: str) -> str:
        """Lấy nội dung của chapter đã chọn từ full_text"""
        chapter_title = self.selected_chapter
        
        # Làm sạch title để tìm kiếm
        clean_title = re.sub(r'^Chapter\s+\d+:\s*', '', chapter_title)
        
        # Tìm vị trí bắt đầu
        start_pos = full_text.find(clean_title)
        if start_pos == -1:
            start_pos = full_text.find(chapter_title)
        if start_pos == -1:
            # Thử tìm từng phần
            parts = chapter_title.split(':')
            if len(parts) > 1:
                start_pos = full_text.find(parts[1].strip())
        
        if start_pos == -1:
            return None
        
        # Tìm vị trí kết thúc (chapter tiếp theo hoặc hết)
        chapter_list = list(self.current_chapters.keys())
        idx = chapter_list.index(chapter_title) if chapter_title in chapter_list else -1
        
        if idx != -1 and idx < len(chapter_list) - 1:
            next_title = chapter_list[idx + 1]
            clean_next = re.sub(r'^Chapter\s+\d+:\s*', '', next_title)
            end_pos = full_text.find(clean_next, start_pos + 1)
            if end_pos == -1:
                end_pos = full_text.find(next_title, start_pos + 1)
        else:
            end_pos = len(full_text)
        
        if end_pos == -1:
            end_pos = len(full_text)
        
        return full_text[start_pos:end_pos].strip()
    
    def translate_selected_chapter(self):
        """Dịch chapter đã chọn"""
        if not self.selected_chapter:
            return
        
        if self.selected_chapter == "ALL":
            self.translate_all_chapters()
            return
        
        # Lấy nội dung
        content = self.current_chapters.get(self.selected_chapter, "")
        
        # Làm sạch text
        content = self.clean_text(content)
        
        # Tách đoạn văn
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            print("❌ Không có nội dung để dịch")
            return
        
        print(f"\n🌐 Đang dịch với {self.model}...")
        translated = self.translator.translate_chapter(
            paragraphs=paragraphs,
            chapter_name=self.selected_chapter,
            batch_size=self.config['translation']['batch_size']
        )
        
        print("\n📝 Đang tạo file Word...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^\w\s-]', '', self.selected_chapter)[:50].replace(' ', '_')
        output_filename = f"{Path(self.current_pdf).stem}_{safe_name}_{timestamp}.docx"
        output_path = Path("output") / output_filename
        
        self.docx_generator.create_translation_document(
            original_paragraphs=paragraphs,
            translated_paragraphs=translated,
            chapter_name=self.selected_chapter,
            output_path=str(output_path),
            images=self.images
        )
        
        print(f"\n✅ DỊCH THÀNH CÔNG!")
        print(f"📁 File: {output_path}")
        print(f"📊 Số đoạn: {len(paragraphs)}")
        print(f"🖼️ Số ảnh: {len(self.images)}")
        
        self.pdf_processor.cleanup_temp_images()
        try:
            os.startfile("output")
        except:
            pass
    
    def translate_all_chapters(self):
        print("\n⏳ Tính năng đang phát triển...")
    
    def clean_text(self, text: str) -> str:
        """Làm sạch văn bản trước khi dịch"""
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n[=_\-*]+\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(
            r'<center>.*?Fig\.\s*(\d+\.\d+)\s*(.*?)</center>',
            r'[IMAGE \1: \2]',
            text,
            flags=re.DOTALL
        )
        text = re.sub(
            r'Table\s+(\d+\.\d+)\s*(.*?)(?=\n\n|\Z)',
            r'[TABLE \1: \2]',
            text,
            flags=re.DOTALL
        )
        return text
    
    def run(self):
        # Bước 1: Chọn file PDF
        if not self.select_pdf():
            return
        
        # Bước 2: Lấy danh sách chapter (KHÔNG TRÍCH XUẤT ẢNH)
        if not self.extract_chapters_only():
            return
        
        # Bước 3: Trích xuất ảnh và nội dung (SAU KHI CHỌN CHAPTER)
        if not self.extract_images_and_content():
            return
        
        # Bước 4: Dịch
        self.translate_selected_chapter()

def main():
    app = BookTranslator()
    app.run()

if __name__ == "__main__":
    main()