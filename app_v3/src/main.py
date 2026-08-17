"""
Ứng dụng dịch sách - Chọn file PDF bằng cửa sổ Windows, chọn chapter, dịch với Gemini 3.5 Flash
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
from paragraph_detector import ParagraphDetector
from translator import GeminiTranslator
from docx_generator import DOCXGenerator

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BookTranslator:
    def __init__(self):
        self.model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')
        self.pdf_processor = PDFProcessor()
        self.paragraph_detector = ParagraphDetector(min_length=50, max_length=3000)
        self.translator = GeminiTranslator(model=self.model)
        
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.docx_generator = DOCXGenerator(self.config['docx'])
        self.current_pdf = None
        self.current_chapters = {}
        self.selected_chapter = None
    
    def select_pdf_gui(self):
        """Mở cửa sổ Windows để chọn file PDF"""
        # Tạo cửa sổ tkinter và ẩn nó đi
        root = Tk()
        root.withdraw()  # Ẩn cửa sổ chính
        
        # Mở hộp thoại chọn file
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF cần dịch",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~\\Desktop")  # Mở từ Desktop
        )
        
        root.destroy()  # Đóng tkinter
        
        if not file_path:
            print("❌ Bạn chưa chọn file nào!")
            return False
        
        if not os.path.exists(file_path):
            print(f"❌ Không tìm thấy file: {file_path}")
            return False
        
        # Kiểm tra đuôi file
        if not file_path.lower().endswith('.pdf'):
            print("❌ Vui lòng chọn file PDF!")
            return False
        
        self.current_pdf = file_path
        print(f"✅ Đã chọn file: {os.path.basename(file_path)}")
        print(f"📁 Đường dẫn: {file_path}")
        return True
    
    def select_pdf_manual(self):
        """Chọn file PDF bằng cách nhập đường dẫn thủ công (fallback)"""
        print("\n📁 Không thể mở cửa sổ chọn file. Vui lòng nhập đường dẫn thủ công:")
        pdf_path = input("📄 Nhập đường dẫn file PDF: ").strip()
        
        if not os.path.exists(pdf_path):
            print(f"❌ Không tìm thấy file: {pdf_path}")
            return False
        
        self.current_pdf = pdf_path
        print(f"✅ Đã chọn: {pdf_path}")
        return True
    
    def select_pdf(self):
        """Chọn file PDF - ưu tiên dùng GUI, nếu lỗi thì dùng thủ công"""
        print("\n" + "=" * 60)
        print("📚 ỨNG DỤNG DỊCH SÁCH TỰ ĐỘNG")
        print("=" * 60)
        
        try:
            # Thử mở cửa sổ chọn file
            return self.select_pdf_gui()
        except Exception as e:
            print(f"⚠️ Không thể mở cửa sổ chọn file: {e}")
            # Fallback: nhập thủ công
            return self.select_pdf_manual()
    
    def extract_chapters(self):
        """Trích xuất và hiển thị danh sách chapter"""
        print("\n📖 Đang đọc file PDF...")
        text = self.pdf_processor.extract_text(self.current_pdf)
        
        if not text:
            print("❌ Không thể trích xuất văn bản")
            return False
        
        print("📑 Đang phát hiện chapter...")
        self.current_chapters = self.pdf_processor.detect_chapters(text)
        
        print(f"\n✅ Tìm thấy {len(self.current_chapters)} chapter:")
        chapter_list = list(self.current_chapters.keys())
        for i, chapter in enumerate(chapter_list, 1):
            content_len = len(self.current_chapters[chapter])
            print(f"  {i}. {chapter} ({content_len} ký tự)")
        
        if not chapter_list:
            print("❌ Không tìm thấy chapter nào")
            return False
        
        # Chọn chapter
        print("\n👉 Nhập số chapter muốn dịch (hoặc 'all' để dịch tất cả):")
        choice = input(f"  (1-{len(chapter_list)} hoặc 'all'): ").strip()
        
        if choice.lower() == 'all':
            print("✅ Sẽ dịch tất cả các chapter")
            # Dịch tất cả sẽ được xử lý sau
            self.selected_chapter = "ALL"
            return True
        elif choice.isdigit() and 1 <= int(choice) <= len(chapter_list):
            self.selected_chapter = chapter_list[int(choice) - 1]
            print(f"✅ Đã chọn: {self.selected_chapter}")
            return True
        else:
            print("❌ Lựa chọn không hợp lệ")
            return False
    
    def translate_selected_chapter(self):
        """Dịch chapter đã chọn"""
        if not self.selected_chapter:
            print("❌ Chưa chọn chapter")
            return
        
        if self.selected_chapter == "ALL":
            self.translate_all_chapters()
            return
        
        chapter_content = self.pdf_processor.get_chapter_content(self.selected_chapter)
        
        print("\n📝 Đang tách đoạn văn...")
        paragraphs = self.paragraph_detector.detect(chapter_content)
        print(f"✅ Phát hiện {len(paragraphs)} đoạn văn")
        
        if not paragraphs:
            print("❌ Không có đoạn văn nào để dịch")
            return
        
        # Dịch
        print(f"\n🌐 Bắt đầu dịch với {self.model}...")
        translated = self.translator.translate_chapter(
            paragraphs=paragraphs,
            chapter_name=self.selected_chapter,
            batch_size=self.config['translation']['batch_size']
        )
        
        # Tạo file Word
        print("\n📝 Đang tạo file Word...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^\w\s-]', '', self.selected_chapter).strip().replace(' ', '_')
        output_filename = f"{Path(self.current_pdf).stem}_{safe_name}_{timestamp}.docx"
        output_path = Path("output") / output_filename
        
        self.docx_generator.create_translation_document(
            original_paragraphs=paragraphs,
            translated_paragraphs=translated,
            chapter_name=self.selected_chapter,
            output_path=str(output_path)
        )
        
        print(f"\n✅ DỊCH THÀNH CÔNG!")
        print(f"📁 File: {output_path}")
        print(f"📊 Số đoạn: {len(paragraphs)}")
        
        # Mở thư mục output
        try:
            os.startfile("output")
        except:
            print("📁 Vui lòng mở thư mục output để xem file kết quả")
    
    def translate_all_chapters(self):
        """Dịch tất cả các chapter"""
        print(f"\n📚 Bắt đầu dịch tất cả {len(self.current_chapters)} chapter")
        
        all_paragraphs = []
        all_chapter_names = []
        
        for chapter_name, content in self.current_chapters.items():
            print(f"\n📖 Đang xử lý: {chapter_name}")
            paragraphs = self.paragraph_detector.detect(content)
            print(f"✅ {len(paragraphs)} đoạn văn")
            
            # Dịch từng chapter
            translated = self.translator.translate_chapter(
                paragraphs=paragraphs,
                chapter_name=chapter_name,
                batch_size=self.config['translation']['batch_size']
            )
            
            # Tạo file riêng cho từng chapter
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^\w\s-]', '', chapter_name).strip().replace(' ', '_')
            output_filename = f"{Path(self.current_pdf).stem}_{safe_name}_{timestamp}.docx"
            output_path = Path("output") / output_filename
            
            self.docx_generator.create_translation_document(
                original_paragraphs=paragraphs,
                translated_paragraphs=translated,
                chapter_name=chapter_name,
                output_path=str(output_path)
            )
            
            print(f"✅ Đã tạo: {output_path}")
        
        print(f"\n✅ DỊCH TẤT CẢ THÀNH CÔNG!")
        try:
            os.startfile("output")
        except:
            print("📁 Vui lòng mở thư mục output để xem file kết quả")
    
    def run(self):
        """Chạy ứng dụng"""
        # Bước 1: Chọn file PDF
        if not self.select_pdf():
            return
        
        # Bước 2: Trích xuất chapter
        if not self.extract_chapters():
            return
        
        # Bước 3: Dịch
        self.translate_selected_chapter()

def main():
    app = BookTranslator()
    app.run()

if __name__ == "__main__":
    main()