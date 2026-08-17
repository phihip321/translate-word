from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List
from pathlib import Path

class DOCXGenerator:
    def __init__(self, config: dict):
        self.config = config
    
    def create_translation_document(self, original: List[str], translated: List[str], 
                                   chapter_name: str, output_path: str) -> str:
        doc = Document()
        
        for section in doc.sections:
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        title = doc.add_heading(chapter_name, level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('_' * 50)
        
        for i, (orig, trans) in enumerate(zip(original, translated), 1):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            
            run = p.add_run(f"{i}. ")
            run.bold = True
            
            if self.config.get('show_original', True):
                run = p.add_run(orig)
                run.font.italic = True
                run.font.color.rgb = RGBColor(100, 100, 100)
                p.add_run('\n')
            
            if self.config.get('show_translation', True):
                run = p.add_run(trans)
                run.bold = True
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        return output_path
