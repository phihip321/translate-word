"""
Phát hiện và tách đoạn văn từ văn bản thô
"""
import re
from typing import List

class ParagraphDetector:
    def __init__(self, min_length: int = 50, max_length: int = 3000):
        self.min_length = min_length
        self.max_length = max_length
    
    def detect(self, text: str) -> List[str]:
        """
        Phát hiện và tách đoạn văn từ văn bản
        """
        if not text:
            return []
        
        # Bước 1: Tách theo xuống dòng kép
        paragraphs = self._split_by_newlines(text)
        
        # Bước 2: Nếu chưa có đoạn nào, tách theo câu (không dùng NLTK để tránh lỗi)
        if len(paragraphs) <= 1:
            paragraphs = self._split_by_sentences_simple(text)
        
        # Bước 3: Lọc và chuẩn hóa
        paragraphs = self._filter_and_clean(paragraphs)
        
        # Bước 4: Xử lý đoạn quá dài
        paragraphs = self._split_long_paragraphs(paragraphs)
        
        # Bước 5: Đảm bảo có ít nhất 1 đoạn
        if not paragraphs:
            paragraphs = [text]
        
        return paragraphs
    
    def _split_by_newlines(self, text: str) -> List[str]:
        """Tách theo dấu xuống dòng"""
        # Tách theo 2 hoặc nhiều xuống dòng
        parts = re.split(r'\n\s*\n+', text.strip())
        # Tách theo xuống dòng đơn nếu văn bản đã được format
        if len(parts) <= 1:
            parts = re.split(r'\n+', text.strip())
        return [p.strip() for p in parts if p.strip()]
    
    def _split_by_sentences_simple(self, text: str) -> List[str]:
        """
        Tách thành các câu đơn giản (không dùng NLTK)
        Dùng regex để tách theo dấu câu
        """
        # Tách theo dấu chấm, chấm hỏi, chấm than
        # Lưu ý: giữ lại các dấu câu
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Nếu số câu ít, thử tách theo dấu chấm phẩy hoặc dấu hai chấm
        if len(sentences) <= 1:
            sentences = re.split(r'(?<=[.:;])\s+(?=[A-Z])', text)
        
        # Nếu vẫn ít, tách theo xuống dòng
        if len(sentences) <= 1:
            sentences = [s.strip() for s in text.split('\n') if s.strip()]
        
        if len(sentences) <= 1:
            sentences = [text]
        
        # Gom các câu ngắn thành đoạn
        paragraphs = []
        current_para = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sent_len = len(sentence)
            
            # Nếu câu quá dài, tách riêng
            if sent_len > self.max_length:
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
                    current_length = 0
                paragraphs.append(sentence)
                continue
            
            # Gom các câu ngắn thành đoạn
            if current_length + sent_len <= self.max_length:
                current_para.append(sentence)
                current_length += sent_len
            else:
                if current_para:
                    paragraphs.append(' '.join(current_para))
                current_para = [sentence]
                current_length = sent_len
        
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        return paragraphs
    
    def _filter_and_clean(self, paragraphs: List[str]) -> List[str]:
        """Lọc và làm sạch đoạn văn"""
        cleaned = []
        
        for para in paragraphs:
            # Loại bỏ khoảng trắng thừa
            para = ' '.join(para.split())
            
            if not para:
                continue
            
            # Bỏ qua đoạn quá ngắn (trừ khi là heading)
            if len(para) < self.min_length and not self._is_heading(para):
                # Nếu quá ngắn, gộp vào đoạn trước
                if cleaned:
                    cleaned[-1] = cleaned[-1] + ' ' + para
                else:
                    cleaned.append(para)
            else:
                cleaned.append(para)
        
        return cleaned
    
    def _is_heading(self, text: str) -> bool:
        """Kiểm tra có phải heading không"""
        if not text:
            return False
        
        words = text.split()
        if len(words) < 10 and not any(c in text for c in '.!?;:'):
            # Có thể là số hoặc từ viết hoa
            if any(c.isupper() for c in text) or any(c.isdigit() for c in text):
                return True
        return False
    
    def _split_long_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Tách đoạn quá dài thành nhiều đoạn nhỏ"""
        result = []
        
        for para in paragraphs:
            if len(para) <= self.max_length:
                result.append(para)
            else:
                # Tách theo dấu câu
                sentences = self._split_by_sentences_simple(para)
                temp_para = []
                temp_len = 0
                
                for sent in sentences:
                    sent_len = len(sent)
                    if temp_len + sent_len <= self.max_length:
                        temp_para.append(sent)
                        temp_len += sent_len
                    else:
                        if temp_para:
                            result.append(' '.join(temp_para))
                        temp_para = [sent]
                        temp_len = sent_len
                
                if temp_para:
                    result.append(' '.join(temp_para))
        
        return result