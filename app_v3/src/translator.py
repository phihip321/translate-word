import google.generativeai as genai
from typing import List
import time
import re
from tqdm import tqdm

class GeminiTranslator:
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def translate_book(self, paragraphs: List[str], batch_size: int = 10, 
                      max_chars_per_batch: int = 4000,
                      source_lang: str = "English", target_lang: str = "Vietnamese") -> List[str]:
        all_translations = []
        batches = self._create_batches(paragraphs, batch_size, max_chars_per_batch)
        
        print(f"📚 Dịch {len(paragraphs)} paragraph thành {len(batches)} batch")
        
        for i, batch in enumerate(tqdm(batches, desc="Đang dịch")):
            translated = self._translate_with_retry(batch, source_lang, target_lang)
            all_translations.extend(translated)
            if i < len(batches) - 1:
                time.sleep(1)
        return all_translations
    
    def _translate_with_retry(self, paragraphs: List[str], source_lang: str, 
                             target_lang: str, max_retries: int = 3) -> List[str]:
        for attempt in range(max_retries):
            try:
                return self._translate_batch(paragraphs, source_lang, target_lang)
            except Exception as e:
                print(f"⚠️ Lỗi lần {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
        return paragraphs.copy()
    
    def _translate_batch(self, paragraphs: List[str], source_lang: str, target_lang: str) -> List[str]:
        prompt = f"""Translate from {source_lang} to {target_lang}. Return ONLY translations, each numbered [1], [2], etc.

{chr(10).join(f'[{i+1}] {p}' for i, p in enumerate(paragraphs))}

Translations:"""
        
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text, len(paragraphs))
    
    def _parse_response(self, response: str, expected_count: int) -> List[str]:
        translations = []
        pattern = r'\[(\d+)\]\s*(.+?)(?=\n\[|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            trans_dict = {int(idx): text.strip() for idx, text in matches}
            for i in range(1, expected_count + 1):
                translations.append(trans_dict.get(i, "[Translation missing]"))
        else:
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            translations = lines[:expected_count] if len(lines) >= expected_count else [response]
        
        while len(translations) < expected_count:
            translations.append("[Translation missing]")
        return translations[:expected_count]
    
    def _create_batches(self, paragraphs: List[str], batch_size: int, max_chars: int) -> List[List[str]]:
        batches = []
        current_batch = []
        current_chars = 0
        
        for para in paragraphs:
            para_len = len(para)
            if para_len > max_chars:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_chars = 0
                batches.append([para])
                continue
            
            if len(current_batch) >= batch_size or current_chars + para_len > max_chars:
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                current_chars = 0
            
            current_batch.append(para)
            current_chars += para_len
        
        if current_batch:
            batches.append(current_batch)
        return batches
