"""
Dich thuat voi Gemini 3.5 Flash
"""
import google.generativeai as genai
from typing import List
import time
import re
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiTranslator:
    def __init__(self, model: str = "gemini-3.5-flash"):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("❌ Khong tim thay GEMINI_API_KEY trong file .env")
        
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        print(f"✅ Da ket noi voi {model}")
    
    def translate_chapter(self, paragraphs: List[str], 
                          chapter_name: str,
                          batch_size: int = 10) -> List[str]:
        """Dich chapter"""
        all_translations = []
        batches = self._create_batches(paragraphs, batch_size, 4000)
        
        print(f"\n📚 Dich chapter: {chapter_name}")
        print(f"📊 {len(paragraphs)} doan, chia thanh {len(batches)} batch")
        
        for i, batch in enumerate(tqdm(batches, desc="Dang dich")):
            translated = self._translate_with_retry(batch)
            all_translations.extend(translated)
            if i < len(batches) - 1:
                time.sleep(0.5)
        
        return all_translations
    
    def _translate_with_retry(self, paragraphs: List[str], max_retries: int = 3) -> List[str]:
        for attempt in range(max_retries):
            try:
                return self._translate_batch(paragraphs)
            except Exception as e:
                print(f"⚠️ Loi lan {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
        print(f"❌ Dich that bai")
        return paragraphs.copy()
    
    def _translate_batch(self, paragraphs: List[str]) -> List[str]:
        prompt = f"""You are a professional translator. Translate from English to Vietnamese.

RULES:
1. Paragraphs: Translate normally.
2. Images: KEEP [IMAGE X: caption] unchanged. Translate caption. Change Fig. X.X -> Hinh X.X.
3. Tables: KEEP [TABLE X: ...] unchanged.
4. References: DO NOT translate [1], [2], etc.

Format: [1] translation 1, [2] translation 2, ...

Text:
{chr(10).join(f'[{i+1}] {p}' for i, p in enumerate(paragraphs))}

Translations:"""
        
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "max_output_tokens": 4000,
            }
        )
        return self._parse_response(response.text, len(paragraphs))
    
    def _parse_response(self, response: str, expected_count: int) -> List[str]:
        translations = []
        pattern = r'\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            trans_dict = {int(idx): text.strip() for idx, text in matches}
            for i in range(1, expected_count + 1):
                translations.append(trans_dict.get(i, "[Missing]"))
        else:
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            translations = lines[:expected_count] if len(lines) >= expected_count else [response]
        
        while len(translations) < expected_count:
            translations.append("[Missing]")
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
