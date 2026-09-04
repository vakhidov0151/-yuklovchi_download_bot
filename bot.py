@dp.message()
async def handle_message(message: types.Message):
    lang = db.get_language(message.from_user.id)
    text = message.text
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await message.answer(_(lang, 'wait_video'))
        
        try:
            info = await asyncio.wait_for(get_video_info(text), timeout=20.0)
        except asyncio.TimeoutError:
            await wait_msg.edit_text("❌ Tarmoq xatosi: Qidiruv vaqti tugadi. Iltimos qaytadan urinib ko'ring.")
            return
        except Exception as e:
            await wait_msg.edit_text(f"❌ Xatolik: {e}")
            return
            
        if not info:
            await wait_msg.edit_text(_(lang, 'not_found'))
            return

        title = info.get('title', 'Video')
        duration = info.get('duration', 0)
        extractor = info.get('extractor', 'Unknown')
        
        video_id = str(uuid.uuid4())[:8]
        c_item = {
            'url': text,
            'thumbnail': info.get('thumbnail')
        }
        url_cache[video_id] = c_item
        db.set_cache(video_id, c_item)
        
        # Instagram, TikTok va YouTube Shorts bo'lsa darhol videoni yuklab beramiz!
        is_direct = ('instagram.com' in text) or ('tiktok.com' in text) or ('/shorts/' in text)
        if is_direct:
            if not db.check_limit(message.from_user.id):
                await wait_msg.edit_text(_(lang, 'limit_over'))
                return
                
            await wait_msg.edit_text(_(lang, 'downloading'))
            try:
                file_path, v_title = await asyncio.wait_for(download_media(text, media_type='video'), timeout=180.0)
                if os.path.getsize(file_path) > 49.5 * 1024 * 1024:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await wait_msg.edit_text("❌ Ushbu video hajmi 50 MB dan katta bo'lgani uchun Telegram orqali yuborib bo'lmadi.")
                    return
                    
                clean_title = re.sub(r'[\\/*?:"<>|\n\r]', '', str(v_title))[:50].strip() or "video"
                video = FSInputFile(file_path, filename=f"{clean_title}.mp4")
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🎵 Musiqasi (Audio)", callback_data=f"dl_aud_{video_id}"),
                        InlineKeyboardButton(text="🧠 AI Konspekt", callback_data=f"ai_sumurl_{video_id}")
                    ]
                ])
                
                await message.answer_video(video=video, caption=f"🎬 <b>{html.escape(str(v_title)[:100])}</b>", reply_markup=keyboard)
                await wait_msg.delete()
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.add_download(message.from_user.id)
                return
            except Exception as e:
                logging.error(f"Direct download error: {e}")
        
        # Agar uzun YouTube video bo'lsa sifat tanlash tugmalarini chiqaramiz
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=_(lang, 'ai_summary_btn_audio'), callback_data=f"ai_sumurl_{video_id}")
            ],
            [
                InlineKeyboardButton(text="⬇️ 1080p", callback_data=f"dl_vid_{video_id}_1080"),
                InlineKeyboardButton(text="⬇️ 720p", callback_data=f"dl_vid_{video_id}_720")
            ],
            [
                InlineKeyboardButton(text="⬇️ 480p", callback_data=f"dl_vid_{video_id}_480"),
                InlineKeyboardButton(text="⬇️ 360p", callback_data=f"dl_vid_{video_id}_360")
            ],
            [
                InlineKeyboardButton(text="🎵 Audio", callback_data=f"dl_aud_{video_id}"),
                InlineKeyboardButton(text="🖼 Thumbnail", callback_data=f"dl_pic_{video_id}")
            ]
        ])
        
        mins, secs = divmod(duration or 0, 60)
        time_str = f"{mins}:{secs:02d}"
        
        await wait_msg.edit_text(_(lang, 'video_caption', title=title, ext=extractor, time=time_str), reply_markup=keyboard)
    else:
         await message.answer(_(lang, 'send_only_link'))
