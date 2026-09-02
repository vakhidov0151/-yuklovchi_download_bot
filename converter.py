import os
import asyncio
from pdf2docx import Converter
import pdfplumber
import pandas as pd
from PIL import Image

try:
    from docx2pdf import convert as d2p
    HAS_D2P = True
except ImportError:
    HAS_D2P = False

async def convert_pdf_to_docx(pdf_path, docx_path):
    def _convert():
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
    await asyncio.to_thread(_convert)
    return docx_path

async def convert_docx_to_pdf(docx_path, pdf_path):
    if not HAS_D2P:
        raise Exception("Ushbu serverda Word'dan PDF'ga o'girish imkoni yo'q (Faqat Windows'da ishlaydi).")
        
    def _convert():
        # docx2pdf uchun absolyut yo'llar tavsiya etiladi
        abs_in = os.path.abspath(docx_path)
        abs_out = os.path.abspath(pdf_path)
        d2p(abs_in, abs_out)
    await asyncio.to_thread(_convert)
    return pdf_path

async def convert_pdf_to_xlsx(pdf_path, xlsx_path):
    def _convert():
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        all_tables.extend(table)
                        # Bo'sh qator qo'shish
                        all_tables.append([""] * len(table[0]))
            
            if not all_tables:
                return False
                
            df = pd.DataFrame(all_tables)
            df.to_excel(xlsx_path, index=False, header=False)
            return True
    return await asyncio.to_thread(_convert)

async def convert_image_to_pdf(img_path, pdf_path):
    def _convert():
        image = Image.open(img_path)
        img_converted = image.convert('RGB')
        img_converted.save(pdf_path)
    await asyncio.to_thread(_convert)
    return pdf_path
