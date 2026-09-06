import asyncio
import os
import time
from google import genai
from config import GEMINI_API_KEY

def get_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        '.mp3': 'audio/mp3',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.opus': 'audio/opus',
        '.aac': 'audio/aac',
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    return mapping.get(ext, 'audio/mp4')

async def summarize_media(file_path: str, prompt: str) -> str:
    """
    Uploads a media file (audio/video) to Gemini File API using the new SDK,
    waits for it to be processed, and returns the generated text based on the prompt.
    """
    def _process():
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        mime_type = get_mime_type(file_path)
        
        # Upload the file with explicit mime_type
        uploaded_file = client.files.upload(
            file=file_path,
            config={'mime_type': mime_type}
        )
        
        # Wait for the file to be processed
        while uploaded_file.state == 'PROCESSING':
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state == 'FAILED':
            raise ValueError("Gemini failed to process the file.")
            
        # Call the model
        from google.genai.errors import ServerError
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[uploaded_file, prompt]
            )
        except ServerError as e:
            if e.code == 503:
                # Fallback to an older/more stable model if 3.6 is under high demand
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[uploaded_file, prompt]
                )
            else:
                raise
        
        # Clean up
        client.files.delete(name=uploaded_file.name)
        
        return response.text
        
    return await asyncio.to_thread(_process)

async def chat_or_translate(text: str, lang: str = 'uz') -> str:
    """Pro-tarjimon va aqlli suhbat funksiyasi"""
    def _process():
        client = genai.Client(api_key=GEMINI_API_KEY)
        sys_prompt = "Sen aqlli suhbatdosh va pro-tarjimonsan. Agar foydalanuvchi matn yuborsa, uning qaysi tildaligini aniqla va ma'nosini buzmay mukammal tarzda tarjima qilib ber (agar o'zbekcha yozsa rus/inglizga, agar boshqa tilda yozsa o'zbekchaga). Agar matn tarjima emas, balki aniq bir savol yoki suhbat bo'lsa, xuddi odamdek aqlli va to'liq javob ber. Javoblaring asosan o'zbek tilida bo'lsin."
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=text,
                config={'system_instruction': sys_prompt}
            )
            return response.text
        except Exception as e:
            return f"❌ AI xatosi: {e}"
            
    return await asyncio.to_thread(_process)

async def summarize_webpage(url: str, lang: str = 'uz') -> str:
    """Maqolalarni o'qib xulosa qilib beruvchi AI"""
    import aiohttp
    from bs4 import BeautifulSoup
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as resp:
                if resp.status != 200:
                    return f"❌ Saytga kirishning imkoni bo'lmadi (Xato kod: {resp.status})"
                html = await resp.text()
                
        soup = BeautifulSoup(html, 'html.parser')
        # Barcha script va style larni olib tashlaymiz
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Matnni qisqartiramiz (Gemini prompt limitiga tushish uchun)
        text = text[:15000]
        
        if len(text) < 100:
            return "❌ Bu saytda yetarlicha ma'lumot topilmadi yoki u botlardan himoyalangan."
            
        prompt = f"Quyidagi maqola/veb-sahifa matnini o'qib, undagi eng asosiy 3-4 ta fikrni qisqacha xulosa qilib (konspekt qilib) ber. Matn: {text}"
        
        def _process():
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
            
        return await asyncio.to_thread(_process)
        
    except Exception as e:
        return f"❌ Maqolani o'qishda xatolik: {e}"
