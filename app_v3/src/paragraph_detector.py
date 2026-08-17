import re
from typing import List
import nltk
from nltk.tokenize import sent_tokenize

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ParagraphDetector:
    def __init__(self, min_length: int = 50, max_length: int = 3000):
        self.min_length = min_length
        self.max_length = max_length
    
    def detect(self, text: str) -> List[str]:
        paragraphs = self._split_by_newlines(text)
        if len(paragraphs) <= 1:
            paragraphs = self._split_by_sentences(text)
        paragraphs = self._filter_and_clean(paragraphs)
        paragraphs = self._split_long_paragraphs(paragraphs)
        return paragraphs
    
    def _split_by_newlines(self, text: str) -> List[str]:
        parts = re.split(r'\n\s*\n+', text.strip())
        if len(parts) <= 1:
            parts = re.split(r'\n+', text.strip())
        return [p.strip() for p in parts if p.strip()]
    
    def _split_by_sentences(self, text: str) -> List[str]:
        sentences = sent_tokenize(text)
        paragraphs = []
        current_para = []
        current_length = 0
        
        for sentence in sentences:
            sent_len = len(sentence)
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
        cleaned = []
        for para in paragraphs:
            para = ' '.join(para.split())
            if len(para) < self.min_length and not self._is_heading(para):
                if cleaned:
                    cleaned[-1] = cleaned[-1] + ' ' + para
                else:
                    cleaned.append(para)
            else:
                cleaned.append(para)
        return cleaned
    
    def _is_heading(self, text: str) -> bool:
        words = text.split()
        if len(words) < 8 and not any(c in text for c in '.!?;:'):
            if any(c.isupper() for c in text) or any(c.isdigit() for c in text):
                return True
        return False
    
    def _split_long_paragraphs(self, paragraphs: List[str]) -> List[str]:
        result = []
        for para in paragraphs:
            if len(para) <= self.max_length:
                result.append(para)
            else:
                sentences = sent_tokenize(para)
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
