from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Callable, Dict, Any, Awaitable
from config import REQUIRED_CHANNELS
from lang import _
from database import db

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if not REQUIRED_CHANNELS:
            return await handler(event, data)
            
        bot = data['bot']
        user_id = event.from_user.id
        lang = db.get_language(user_id)
        
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            return await handler(event, data)
        
        # Ignored commands/callbacks
        if isinstance(event, Message) and event.text in ['/start', '/lang', '/profile', '/admin', '/cancel']:
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and (event.data.startswith('lang_') or event.data == 'admin_broadcast'):
            return await handler(event, data)
            
        not_subscribed = []
        for channel in REQUIRED_CHANNELS:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ['left', 'kicked', 'not_found']:
                    not_subscribed.append(channel)
            except Exception as e:
                # Bot might not be admin or channel doesn't exist
                print(f"Error checking sub for {channel}: {e}")
                # KANALGA BOT ADMIN QILINMAGAN BO'LSA, xato berishi va o'tkazmasligi kerak!
                not_subscribed.append(channel)
                
        if not_subscribed:
            buttons = []
            for ch in not_subscribed:
                # simple link generation
                invite_link = f"https://t.me/{ch.replace('@', '')}"
                buttons.append([InlineKeyboardButton(text=f"📢 {ch}", url=invite_link)])
                
            buttons.append([InlineKeyboardButton(text=_(lang, 'check_sub_btn'), callback_data="check_sub")])
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            text = _(lang, 'must_subscribe')
            
            if isinstance(event, Message):
                await event.answer(text, reply_markup=markup)
            elif isinstance(event, CallbackQuery):
                if event.data == 'check_sub':
                    await event.answer("❌", show_alert=True)
                else:
                    await event.message.answer(text, reply_markup=markup)
                    await event.answer()
            return
            
        # If user IS subscribed but clicked 'check_sub', let's say success
        if isinstance(event, CallbackQuery) and event.data == 'check_sub':
            await event.answer(_(lang, 'sub_success'), show_alert=True)
            await event.message.delete()
            return
            
        return await handler(event, data)
