import asyncio
import os
import re
import yt_dlp

def _get_info_sync(url: str):
    clean_url = re.sub(r'\?.*$', '', url) if ('instagram.com' in url or 'tiktok.com' in url) else url
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    elif os.path.exists('/app/data/cookies.txt'):
        ydl_opts['cookiefile'] = '/app/data/cookies.txt'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except Exception:
            try:
                return ydl.extract_info(clean_url, download=False)
            except Exception as e:
                print(f"Error getting info: {e}")
                return None

async def get_video_info(url: str):
    return await asyncio.to_thread(_get_info_sync, url)

def _download_media_sync(url: str, media_type: str = 'video', quality: str = None, output_path: str = "downloads"):
    os.makedirs(output_path, exist_ok=True)
    clean_url = re.sub(r'\?.*$', '', url) if ('instagram.com' in url or 'tiktok.com' in url) else url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    ydl_opts = {
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'socket_timeout': 60,
        'http_headers': headers
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    elif os.path.exists('/app/data/cookies.txt'):
        ydl_opts['cookiefile'] = '/app/data/cookies.txt'
        
    if os.path.exists('./ffmpeg.exe'):
        ydl_opts['ffmpeg_location'] = './ffmpeg.exe'
    
    if media_type == 'audio':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    else:
        direct_domains = [
            'instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 
            'threads.net', 'facebook.com', 'fb.watch', 'pinterest.com', 'pin.it'
        ]
        if any(domain in url.lower() for domain in direct_domains):
            ydl_opts['format'] = 'best[ext=mp4]/best'
        elif quality:
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['format_sort'] = ['vcodec:h264', 'acodec:m4a', 'res']
            ydl_opts['format'] = (
                f'bestvideo[height<={quality}]+bestaudio/'
                f'best[height<={quality}]/'
                f'bestvideo[width<={quality}]+bestaudio/'
                f'best[width<={quality}]/'
                f'best'
            )
        else:
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
    info = None
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception:
                info = ydl.extract_info(clean_url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        print(f"Primary download attempt failed: {e}. Trying fallback...")
        fallback_opts = {
            'outtmpl': f'{output_path}/%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'socket_timeout': 60,
            'format': 'best',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web']
                }
            },
            'http_headers': headers
        }
        if os.path.exists('cookies.txt'):
            fallback_opts['cookiefile'] = 'cookies.txt'
        elif os.path.exists('/app/data/cookies.txt'):
            fallback_opts['cookiefile'] = '/app/data/cookies.txt'
            
        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception:
                info = ydl.extract_info(clean_url, download=True)
            filename = ydl.prepare_filename(info)

    # Faylni topish
    if not os.path.exists(filename):
        base, _ = os.path.splitext(filename)
        for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3', '.mov']:
            if os.path.exists(base + ext):
                filename = base + ext
                break
                
    if not os.path.exists(filename):
        files = [os.path.join(output_path, f) for f in os.listdir(output_path)]
        if files:
            filename = max(files, key=os.path.getctime)
                
    return filename, info.get('title', 'Media') if info else 'Media'

async def download_media(url: str, media_type: str = 'video', quality: str = None):
    return await asyncio.to_thread(_download_media_sync, url, media_type, quality)
