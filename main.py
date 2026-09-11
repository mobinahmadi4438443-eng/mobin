import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🧩 ساختار خام دکمه‌ها (فقط با Custom Emoji، بدون رنگ)
# ==========================================
RAW_INLINE_KEYBOARD = [
    # ردیف 1
    [
        {"text": "حساب کاربری", "callback_data": "btn_profile", "icon_custom_emoji_id": "5987865893084861885"},
        {"text": "بازار", "callback_data": "btn_market", "icon_custom_emoji_id": "5258024802010026053"}
    ],
    # ردیف 2
    [
        {"text": "داستانی", "callback_data": "btn_story", "icon_custom_emoji_id": "5364052602357044385"},
        {"text": "مولتی(چند جهانی)", "callback_data": "btn_multi", "icon_custom_emoji_id": "5361741454685256344"}
    ],
    # ردیف 3
    [
        {"text": "اسکین", "callback_data": "btn_skin", "icon_custom_emoji_id": "5987973065403797894"},
        {"text": "ارتقا", "callback_data": "btn_upgrade", "icon_custom_emoji_id": "5375338737028841420"}
    ],
    # ردیف 4 (تکی)
    [
        {"text": "ماموریت ها", "callback_data": "btn_missions", "icon_custom_emoji_id": "5282996373229167849"}
    ],
    # ردیف 5
    [
        {"text": "جنگ ها", "callback_data": "btn_wars", "icon_custom_emoji_id": "5453991094435997597"},
        {"text": "بازار سیاه", "callback_data": "btn_blackmarket", "icon_custom_emoji_id": "5296387887984580731"}
    ],
    # ردیف 6
    [
        {"text": "فروشگاه", "callback_data": "btn_shop", "icon_custom_emoji_id": "5406683434124859552"},
        {"text": "لیدربرد", "callback_data": "btn_leaderboard", "icon_custom_emoji_id": "5415655814079723871"}
    ],
    # ردیف 7
    [
        {"text": "کلن", "callback_data": "btn_clan", "icon_custom_emoji_id": "5978687277390371946"},
        {"text": "اخبار", "callback_data": "btn_news", "icon_custom_emoji_id": "5443038326535759644"}
    ],
    # ردیف 8
    [
        {"text": "راهنما", "callback_data": "btn_help", "icon_custom_emoji_id": "5282843764451195532"},
        {"text": "بستن منو", "callback_data": "btn_close", "icon_custom_emoji_id": "5210952531676504517"}
    ]
]

# ==========================================
# 📡 متد ارسال مستقیم درخواست به API تلگرام
# ==========================================
async def send_empire_menu_raw(chat_id: int, reply_to_message_id: int):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    text = (
        '<tg-emoji emoji-id="5282974228377789040">👑</tg-emoji> <b>منوی اصلی بازی امپراطوری ها</b>\n\n'
        '<tg-emoji emoji-id="5019617635629794161">👇</tg-emoji> بخش مورد نظر خود را انتخاب کنید:'
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_parameters": {"message_id": reply_to_message_id},
        "reply_markup": {
            "inline_keyboard": RAW_INLINE_KEYBOARD
        }
    }
    
    # ارسال Payload خام به تلگرام
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"):
                logging.error(f"Telegram API Error: {result}")

# ==========================================
# 🚀 هندلرهای گروه
# ==========================================
@dp.message(F.text.contains("امپراطوری ها"))
async def trigger_empire_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        # فراخوانی متد اختصاصی برای ارسال دکمه‌های دارای ایموجی متحرک
        await send_empire_menu_raw(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id
        )

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای
# ==========================================
@dp.callback_query(F.data == "btn_close")
async def close_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("منو بسته شد.", show_alert=False)

@dp.callback_query(F.data.startswith("btn_"))
async def handle_other_buttons(callback: types.CallbackQuery):
    if callback.data != "btn_close":
        await callback.answer("⏳ این بخش در حال توسعه است...", show_alert=True)

# ==========================================
# 🔥 اجرای هسته
# ==========================================
async def main():
    print("🤖 ربات روشن شد (دکمه‌های استاندارد با ایموجی متحرک فعال است)...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
