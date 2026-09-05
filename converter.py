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
    import shutil
    import subprocess
    
    if shutil.which("libreoffice"):
        def _convert_libre():
            abs_in = os.path.abspath(docx_path)
            out_dir = os.path.dirname(os.path.abspath(pdf_path))
            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", abs_in, "--outdir", out_dir], check=True)
            base_name = os.path.splitext(os.path.basename(abs_in))[0] + ".pdf"
            gen_pdf = os.path.join(out_dir, base_name)
            if os.path.exists(gen_pdf) and gen_pdf != os.path.abspath(pdf_path):
                os.replace(gen_pdf, pdf_path)
        await asyncio.to_thread(_convert_libre)
        return pdf_path

    if HAS_D2P:
        try:
            def _convert_win():
                abs_in = os.path.abspath(docx_path)
                abs_out = os.path.abspath(pdf_path)
                d2p(abs_in, abs_out)
            await asyncio.to_thread(_convert_win)
            return pdf_path
        except Exception:
            pass

    # Universal Python fallback (Linux/Railway da Word bo'lmaganda ishlaydi)
    def _convert_fallback():
        import docx
        from fpdf import FPDF
        
        doc = docx.Document(docx_path)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                clean = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, clean)
                pdf.ln(2)
        pdf.output(pdf_path)
        
    await asyncio.to_thread(_convert_fallback)
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
