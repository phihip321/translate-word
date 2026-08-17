"""
Xử lý PDF - Trích xuất văn bản, hình ảnh và BOOKMARK
"""
import pdfplumber
import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple
from pathlib import Path
import os

class PDFProcessor:
    def __init__(self):
        self.pages = []
        self.full_text = ""
        self.chapters = {}
        self.images = []
        self.image_counter = 0
        self.pdf_path = None
        self.bookmarks = []
    
    def extract_text_and_images(self, pdf_path: str) -> Tuple[str, List]:
        """Trích xuất văn bản và hình ảnh từ PDF"""
        self.pdf_path = pdf_path
        text_parts = []
        self.images = []
        self.image_counter = 0
        
        doc = fitz.open(pdf_path)
        temp_img_dir = Path("temp_images")
        temp_img_dir.mkdir(exist_ok=True)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    if page_num < len(pdf.pages):
                        page_text = pdf.pages[page_num].extract_text()
                        if page_text:
                            text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
            except:
                pass
            
            image_list = page.get_images(full=True)
            for img in image_list:
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    self.image_counter += 1
                    img_filename = f"img_{page_num + 1}_{self.image_counter}.{image_ext}"
                    img_path = temp_img_dir / img_filename
                    
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)
                    
                    self.images.append({
                        "page": page_num + 1,
                        "img_index": self.image_counter,
                        "path": str(img_path),
                        "filename": img_filename,
                        "ext": image_ext
                    })
                except:
                    pass
        
        doc.close()
        self.full_text = "\n\n".join(text_parts)
        return self.full_text, self.images
    
    def extract_text(self, pdf_path: str) -> str:
        self.pdf_path = pdf_path
        text_parts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"[Page {page_num}]\n{text}")
        except:
            return ""
        self.full_text = "\n\n".join(text_parts)
        return self.full_text
    
    def get_bookmarks(self) -> List[Dict]:
        """Lấy bookmark từ PDF"""
        if not self.pdf_path:
            return []
        
        doc = fitz.open(self.pdf_path)
        toc = doc.get_toc()
        doc.close()
        
        bookmarks = []
        for item in toc:
            bookmarks.append({
                "level": item[0],
                "title": item[1],
                "page": item[2]
            })
        
        self.bookmarks = bookmarks
        return bookmarks
    
    def detect_chapters(self, text: str = None) -> Dict[str, str]:
        """
        PHÁT HIỆN CHAPTER - ƯU TIÊN BOOKMARK
        """
        # ===== CÁCH 1: ĐỌC TỪ BOOKMARK =====
        bookmarks = self.get_bookmarks()
        
        if bookmarks:
            print(f"📑 Đọc từ Bookmark: {len(bookmarks)} mục")
            
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
            
            # Nếu tìm thấy chapter từ bookmark
            if chapters:
                # Lấy nội dung cho từng chapter
                if self.full_text:
                    chapters = self._extract_content_for_chapters(chapters)
                
                self.chapters = chapters
                return chapters
        
        # ===== CÁCH 2: TỰ DETECT TỪ HEADING =====
        print("📑 Không có Bookmark, tự detect từ heading...")
        
        if text is None:
            text = self.full_text
        if not text:
            return {"Full Book": ""}
        
        chapters = self._detect_from_headings(text)
        self.chapters = chapters
        return chapters
    
    def _extract_content_for_chapters(self, chapters: Dict[str, str]) -> Dict[str, str]:
        """Lấy nội dung cho từng chapter từ full_text"""
        result = {}
        chapter_list = list(chapters.keys())
        
        for i, title in enumerate(chapter_list):
            # Tìm vị trí bắt đầu
            clean_title = re.sub(r'^Chapter\s+\d+:\s*', '', title)
            start_pos = self.full_text.find(clean_title)
            if start_pos == -1:
                start_pos = self.full_text.find(title)
            
            # Tìm vị trí kết thúc
            end_pos = len(self.full_text)
            if i < len(chapter_list) - 1:
                next_title = chapter_list[i + 1]
                clean_next = re.sub(r'^Chapter\s+\d+:\s*', '', next_title)
                end_pos = self.full_text.find(clean_next, start_pos + 1) if start_pos != -1 else -1
                if end_pos == -1:
                    end_pos = self.full_text.find(next_title, start_pos + 1) if start_pos != -1 else -1
                if end_pos == -1:
                    end_pos = len(self.full_text)
            
            if start_pos != -1:
                result[title] = self.full_text[start_pos:end_pos].strip()
            else:
                result[title] = ""
        
        return result
    
    def _detect_from_headings(self, text: str) -> Dict[str, str]:
        """Tự detect chapter từ heading"""
        lines = text.split('\n')
        
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\s*\d+\s*$', line):
                continue
            if len(line.split()) < 3 and ':' not in line and '.' not in line:
                continue
            filtered_lines.append(line)
        
        patterns = [
            r'(?i)^\s*(?:chapter|chương)\s+(\d+|[IVXLCDM]+)\s*[:.]?\s*(.*?)$',
            r'(?i)^\s*(?:chapter|chương)\s+(\d+|[IVXLCDM]+)\s*$',
            r'^\s*(\d+)\s*[.:]\s*([A-Z][^\n]{5,80})$',
            r'^\s*([IVXLCDM]+)\s*[.:]\s*([A-Z][^\n]{5,80})$',
        ]
        
        chapters = {}
        current_title = "Introduction"
        current_content = []
        found_first = False
        
        for line in filtered_lines:
            is_chapter = False
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if len(groups) >= 2 and groups[1] and len(groups[1]) < 100:
                        chapter_title = f"Chapter {groups[0]}: {groups[1].strip()}"
                    elif len(groups) >= 1:
                        chapter_title = f"Chapter {groups[0]}"
                    else:
                        continue
                    
                    if found_first and current_title and current_content:
                        chapters[current_title] = '\n'.join(current_content).strip()
                    
                    current_title = chapter_title
                    current_content = []
                    found_first = True
                    is_chapter = True
                    break
            
            if not is_chapter and found_first:
                current_content.append(line)
        
        if found_first and current_title and current_content:
            chapters[current_title] = '\n'.join(current_content).strip()
        
        if not chapters:
            chapters = {"Full Book": text}
        
        return chapters
    
    def get_chapter_content(self, chapter_title: str) -> str:
        return self.chapters.get(chapter_title, "")
    
    def cleanup_temp_images(self):
        import shutil
        temp_dir = Path("temp_images")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)