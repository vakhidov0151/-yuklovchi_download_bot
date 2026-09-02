import asyncio
import os
import time
from google import genai
from config import GEMINI_API_KEY

async def summarize_media(file_path: str, prompt: str) -> str:
    """
    Uploads a media file (audio/video) to Gemini File API using the new SDK,
    waits for it to be processed, and returns the generated text based on the prompt.
    """
    def _process():
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Upload the file
        uploaded_file = client.files.upload(file=file_path)
        
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
