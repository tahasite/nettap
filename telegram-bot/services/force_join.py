from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from config import FORCE_JOIN_CHANNELS

async def check_user_joined(bot: Bot, user_id: int) -> tuple:
    channels = FORCE_JOIN_CHANNELS()
    not_joined = []
    
    if not channels:
        return True, []
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(channel)
        except TelegramError:
            not_joined.append(channel)
    
    is_joined = len(not_joined) == 0
    return is_joined, not_joined

def build_join_keyboard(not_joined_channels: list) -> InlineKeyboardMarkup:
    buttons = []
    
    for channel in not_joined_channels:
        channel_username = channel.replace("@", "")
        buttons.append([
            InlineKeyboardButton(
                text=f"🔗 عضویت در {channel}",
                url=f"https://t.me/{channel_username}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="✅ عضو شدم، بررسی کن", callback_data="check_join")
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_join_message() -> str:
    channels = FORCE_JOIN_CHANNELS()
    channels_list = "\n".join([f"🔹 {ch}" for ch in channels])
    return (
        "🔒 <b>عضویت اجباری</b>\n\n"
        "برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شو:\n\n"
        f"{channels_list}\n\n"
        "پس از عضویت، دکمه «عضو شدم» را بزن ✅"
    )