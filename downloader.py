import asyncio
import os
import yt_dlp

def _get_info_sync(url: str):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'socket_timeout': 15,
    }
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    elif os.path.exists('/app/data/cookies.txt'):
        ydl_opts['cookiefile'] = '/app/data/cookies.txt'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            print(f"Error getting info: {e}")
            return None

async def get_video_info(url: str):
    return await asyncio.to_thread(_get_info_sync, url)

def _download_media_sync(url: str, media_type: str, quality: str = None, output_path: str = "downloads"):
    os.makedirs(output_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'merge_output_format': 'mp4', # Har doim Telegram o'qiydigan MP4 formatida qilib beradi
        'format_sort': ['vcodec:h264', 'acodec:m4a', 'res'], # Qora ekran muammosini hal qilish uchun eng universal Codec'larni tanlash
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    elif os.path.exists('/app/data/cookies.txt'):
        ydl_opts['cookiefile'] = '/app/data/cookies.txt'
        
    if os.path.exists('./ffmpeg.exe'):
        ydl_opts['ffmpeg_location'] = './ffmpeg.exe'
    
    if media_type == 'audio':
        # Audio uchun eng kichik hajmli sifat (m4a formatida, Telegram yaxshi o'qiydi va hajm ~10MB gacha bo'ladi)
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        # AI tahlili uchun katta audiolarga ham ruxsat beramiz (Telegram orqali yuborilmasa limit kerak emas)
        ydl_opts['max_filesize'] = 500 * 1024 * 1024 # 500MB
    else:
        ydl_opts['max_filesize'] = 50 * 1024 * 1024 # 50MB limit (Telegram upload limit)
        if quality:
            # Agar sifat so'ralsa (masalan 720, 1080)
            ydl_opts['format'] = f'best[height<={quality}]/bestvideo[height<={quality}]+bestaudio/best'
        else:
            ydl_opts['format'] = 'best'
            
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        # Bazi hollarda yt-dlp fayl kengaytmasini o'zgartirishi mumkin, uni topamiz
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break
                    
        title = info.get('title', 'video')
        return filename, title

async def download_media(url: str, media_type: str, quality: str = None, output_path: str = "downloads"):
    return await asyncio.to_thread(_download_media_sync, url, media_type, quality, output_path)
