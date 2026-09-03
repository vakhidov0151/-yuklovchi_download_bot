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
