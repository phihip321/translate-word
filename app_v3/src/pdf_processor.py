"""
Xử lý PDF và trích xuất chapter
"""
import pdfplumber
import re
from typing import List, Dict, Optional

class PDFProcessor:
    def __init__(self):
        self.pages = []
        self.full_text = ""
        self.chapters = {}
    
    def extract_text(self, pdf_path: str) -> str:
        """Trích xuất toàn bộ văn bản từ PDF"""
        text_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                        self.pages.append({
                            'page_num': page_num,
                            'text': text
                        })
        except Exception as e:
            print(f"⚠️ Lỗi đọc PDF: {e}")
            return ""
        
        self.full_text = '\n\n'.join(text_parts)
        return self.full_text
    
    def detect_chapters(self, text: str = None) -> Dict[str, str]:
        """
        Phát hiện và tách các chapter
        Trả về: {chapter_title: chapter_content}
        """
        if text is None:
            text = self.full_text
        
        if not text:
            print("⚠️ Không có văn bản để phát hiện chapter")
            return {"Full Book": ""}
        
        # Các pattern thường gặp của chapter
        patterns = [
            r'(?i)(?:chapter|chương|part|phần)\s+(\d+|[IVXLCDM]+)\s*[:.]?\s*([^\n]*)',
            r'(?i)(?:chapter|chương|part|phần)\s+(\d+|[IVXLCDM]+)',
            r'(?i)^\s*(\d+|[IVXLCDM]+)\s*[.:]\s*([^\n]+)',
            r'(?i)(?:chapter|chương)\s+(one|two|three|four|five|six|seven|eight|nine|ten)',
        ]
        
        chapters = {}
        lines = text.split('\n')
        
        current_chapter = "Introduction"
        current_content = []
        found_first = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_chapter = False
            chapter_title = None
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Lấy số chapter và tiêu đề
                    if len(match.groups()) >= 1:
                        chapter_num = match.group(1) if match.groups() else "1"
                        chapter_title = f"Chapter {chapter_num}"
                        if len(match.groups()) > 1 and match.group(2):
                            chapter_title += f": {match.group(2).strip()}"
                    
                    # Lưu chapter trước đó
                    if found_first and current_content:
                        chapters[current_chapter] = '\n'.join(current_content)
                    
                    current_chapter = chapter_title
                    current_content = []
                    found_first = True
                    is_chapter = True
                    break
            
            if not is_chapter:
                current_content.append(line)
        
        # Lưu chapter cuối cùng
        if found_first and current_content:
            chapters[current_chapter] = '\n'.join(current_content)
        
        # Nếu không tìm thấy chapter nào, lấy toàn bộ
        if not chapters:
            chapters = {"Full Book": text}
        
        self.chapters = chapters
        return chapters
    
    def get_chapter_content(self, chapter_title: str) -> str:
        """Lấy nội dung của một chapter"""
        return self.chapters.get(chapter_title, "")
    
    def get_all_chapters(self) -> Dict[str, str]:
        """Lấy tất cả chapters"""
        return self.chapters