import os
import yaml
import logging
from pathlib import Path
from datetime import datetime
from pdf_processor import PDFProcessor
from paragraph_detector import ParagraphDetector
from translator import GeminiTranslator
from docx_generator import DOCXGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BookTranslator:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.pdf_processor = PDFProcessor(self.config['pdf']['method'])
        self.paragraph_detector = ParagraphDetector(
            self.config['pdf']['min_paragraph_length'],
            self.config['pdf']['max_paragraph_chars']
        )
        
        api_key = self.config['translation']['api_key']
        if not api_key:
            api_key = input("🔑 Nhập Gemini API key: ")
        
        self.translator = GeminiTranslator(api_key, self.config['translation']['model'])
        self.docx_generator = DOCXGenerator(self.config['docx'])
    
    def translate_book(self, pdf_path: str, output_dir: str = "output"):
        logger.info(f"📖 Bắt đầu dịch: {pdf_path}")
        
        text = self.pdf_processor.extract_text(pdf_path)
        if not text:
            logger.error("❌ Không thể trích xuất văn bản")
            return
        
        paragraphs = self.paragraph_detector.detect(text)
        logger.info(f"✅ Phát hiện {len(paragraphs)} đoạn văn")
        
        translated = self.translator.translate_book(
            paragraphs,
            self.config['translation']['batch_size'],
            self.config['translation']['max_chars_per_batch'],
            self.config['translation']['source_lang'],
            self.config['translation']['target_lang']
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"{Path(pdf_path).stem}_translated_{timestamp}.docx"
        
        self.docx_generator.create_translation_document(
            paragraphs, translated, Path(pdf_path).stem, str(output_file)
        )
        
        logger.info(f"✅ Đã tạo: {output_file}")
        return {'output_file': str(output_file), 'total_paragraphs': len(paragraphs)}

def main():
    print("=" * 60)
    print("📚 ỨNG DỤNG DỊCH SÁCH TỰ ĐỘNG")
    print("=" * 60)
    
    translator = BookTranslator()
    pdf_path = input("📄 Nhập đường dẫn file PDF: ").strip()
    
    if not os.path.exists(pdf_path):
        print(f"❌ Không tìm thấy file: {pdf_path}")
        return
    
    result = translator.translate_book(pdf_path)
    print(f"\n✅ Dịch hoàn tất!")
    print(f"📁 File: {result['output_file']}")

if __name__ == "__main__":
    main()
