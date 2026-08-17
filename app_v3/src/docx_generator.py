"""
Tao file Word tu ban dich
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List, Dict
from pathlib import Path
import re

class DOCXGenerator:
    def __init__(self, config: dict):
        self.config = config
    
    def create_translation_document(self,
                                   original_paragraphs: List[str],
                                   translated_paragraphs: List[str],
                                   chapter_name: str,
                                   output_path: str,
                                   images: List[Dict] = None) -> str:
        doc = Document()
        
        for section in doc.sections:
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
        
        title = doc.add_heading(chapter_name, level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('_' * 50)
        
        for i, (orig, trans) in enumerate(zip(original_paragraphs, translated_paragraphs), 1):
            img_matches = re.findall(r'\[IMAGE (\d+):(.*?)\]', trans)
            
            if img_matches:
                for img_id, caption in img_matches:
                    p = doc.add_paragraph()
                    run = p.add_run(f"Hinh {img_id}: {caption}")
                    run.italic = True
                    run.font.size = Pt(10)
                    p.paragraph_format.space_after = Pt(6)
                    
                    if images:
                        for img in images:
                            if str(img_id) == str(img.get('img_index', '')):
                                try:
                                    doc.add_picture(img['path'], width=Inches(5))
                                    doc.add_paragraph()
                                except:
                                    doc.add_paragraph("(Khong the chen anh)")
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(6)
                
                run = p.add_run(f"{i}. ")
                run.bold = True
                run.font.size = Pt(self.config.get('font_size', 11))
                
                run = p.add_run(trans)
                run.font.name = self.config.get('font_name', 'Times New Roman')
                run.font.size = Pt(self.config.get('font_size', 11))
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        return str(output_path)
