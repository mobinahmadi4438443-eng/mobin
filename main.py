import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, F, types

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🧩 ساختار خام دکمه‌ها (Raw JSON برای API)
# ==========================================

# --- دکمه‌های منوی اصلی ---
RAW_MAIN_KEYBOARD = [
    [
        {"text": "حساب کاربری", "callback_data": "btn_profile", "icon_custom_emoji_id": "5987865893084861885"},
        {"text": "بازار", "callback_data": "btn_market", "icon_custom_emoji_id": "5258024802010026053"}
    ],
    [
        {"text": "داستانی", "callback_data": "btn_story", "icon_custom_emoji_id": "5364052602357044385"},
        {"text": "مولتی(چند جهانی)", "callback_data": "btn_multi", "icon_custom_emoji_id": "5361741454685256344"}
    ],
    [
        {"text": "اسکین", "callback_data": "btn_skin", "icon_custom_emoji_id": "5987973065403797894"},
        {"text": "ارتقا", "callback_data": "btn_upgrade", "icon_custom_emoji_id": "5375338737028841420"}
    ],
    [
        {"text": "ماموریت ها", "callback_data": "btn_missions", "icon_custom_emoji_id": "5282996373229167849"}
    ],
    [
        {"text": "جنگ ها", "callback_data": "btn_wars", "icon_custom_emoji_id": "5453991094435997597"},
        {"text": "بازار سیاه", "callback_data": "btn_blackmarket", "icon_custom_emoji_id": "5296387887984580731"}
    ],
    [
        {"text": "فروشگاه", "callback_data": "btn_shop", "icon_custom_emoji_id": "5406683434124859552"},
        {"text": "لیدربرد", "callback_data": "btn_leaderboard", "icon_custom_emoji_id": "5415655814079723871"}
    ],
    [
        {"text": "کلن", "callback_data": "btn_clan", "icon_custom_emoji_id": "5978687277390371946"},
        {"text": "اخبار", "callback_data": "btn_news", "icon_custom_emoji_id": "5443038326535759644"}
    ],
    [
        {"text": "راهنما", "callback_data": "btn_help", "icon_custom_emoji_id": "5282843764451195532"},
        {"text": "بستن منو", "callback_data": "btn_close", "icon_custom_emoji_id": "5210952531676504517"}
    ]
]

# --- دکمه‌های بخش داستانی ---
RAW_STORY_KEYBOARD = [
    [
        {"text": "ادامه بازی", "callback_data": "btn_continue_story", "icon_custom_emoji_id": "5206607081334906820"},
        {"text": "بازگشت", "callback_data": "btn_back_main", "icon_custom_emoji_id": "5210952531676504517"}
    ]
]

# ==========================================
# 📝 متن‌های ربات (همراه با ایموجی‌های متحرک)
# ==========================================

MAIN_TEXT = (
    '<tg-emoji emoji-id="5282974228377789040">👑</tg-emoji> <b>منوی اصلی بازی تاتاروس</b>\n\n'
    '<tg-emoji emoji-id="5019617635629794161">👇</tg-emoji> بخش مورد نظر خود را انتخاب کنید:'
)

STORY_TEXT = (
    'سلام <tg-emoji emoji-id="5296480809602023717">👋</tg-emoji>\n'
    'به بازی تاتاروس خوش آمدید <tg-emoji emoji-id="5296349143084595007">🎮</tg-emoji>\n\n'
    'با فشار دادن/کلیک کردن روی دکمه شروع وارد دنیای فراموش شده میشید.<tg-emoji emoji-id="5303073678890662588">🌍</tg-emoji>\n\n'
    'دنیای فراموش شده جای افرادیه که در دنیای خودشون مرتکب اشتباهات زیادی شدن و تبعید شدن به دنیای فراموش شده.<tg-emoji emoji-id="5296785692150497491">⛓</tg-emoji>\n\n'
    'برای اینکه بتونید از دنیای فراموش شده فرار کنید مجموعه ای از ماموریت ها و دشمن های مختلفی رو باید پشت سر بزارید.<tg-emoji emoji-id="5453991094435997597">⚔️</tg-emoji>\n\n'
    'باید در طول انجام ماموریت و مبارزه حواستون باشه که نیازمند هستید به منابع مختلف،\n'
    'مثل سکه، الماس و ...<tg-emoji emoji-id="5213094908608392768">💎</tg-emoji>\n\n'
    '<tg-emoji emoji-id="5395695537687123235">⚡️</tg-emoji> در طول مبارزات به شما مقدار قابل توجهی منابع تعلق میگیره ولی همیشه به این معنا نیست که قراره کافی باشن پس بهتره به بخش ماموریت ها هم سر بزنید <tg-emoji emoji-id="5395695537687123235">⚡️</tg-emoji>\n\n'
    'اولین دشمن شما دراخور هستش برای کشتن اون نیاز به\n\n'
    ' 45،000 سکه دارید <tg-emoji emoji-id="5282996373229167849">🪙</tg-emoji>\n\n'
    'و 1750 XP خون لازم دارید 🩸\n\n'
    'دراخور دشمن ساده ای نیست پس حواستو جمع کن تو دامش نیوفتی <tg-emoji emoji-id="5440660757194744323">⚠️</tg-emoji>'
)

# ==========================================
# 📡 متد جامع ارسال درخواست خام به تلگرام
# ==========================================
async def send_raw_api(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"):
                logging.error(f"Telegram API Error: {result}")

# ==========================================
# 🚀 هندلرهای گروه (فراخوانی ربات)
# ==========================================
# تغییر کلمه کلیدی از امپراطوری ها به تاتاروس
@dp.message(F.text.contains("تاتاروس"))
async def trigger_tatarus_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        payload = {
            "chat_id": message.chat.id,
            "text": MAIN_TEXT,
            "parse_mode": "HTML",
            "reply_parameters": {"message_id": message.message_id},
            "reply_markup": {
                "inline_keyboard": RAW_MAIN_KEYBOARD
            }
        }
        await send_raw_api("sendMessage", payload)

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای
# ==========================================

# --- هندلر کلیک روی دکمه داستانی ---
@dp.callback_query(F.data == "btn_story")
async def open_story_menu(callback: types.CallbackQuery):
    payload = {
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id,
        "text": STORY_TEXT,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": RAW_STORY_KEYBOARD
        }
    }
    # استفاده از متد editMessageText برای تغییر ظاهر همان پیام قبلی
    await send_raw_api("editMessageText", payload)
    await callback.answer()

# --- هندلر بازگشت به منوی اصلی ---
@dp.callback_query(F.data == "btn_back_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    payload = {
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id,
        "text": MAIN_TEXT,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": RAW_MAIN_KEYBOARD
        }
    }
    await send_raw_api("editMessageText", payload)
    await callback.answer()

# --- هندلر بستن منو ---
@dp.callback_query(F.data == "btn_close")
async def close_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("منو بسته شد.", show_alert=False)

# --- هندلر سایر دکمه‌های در حال ساخت ---
@dp.callback_query(F.data.startswith("btn_"))
async def handle_other_buttons(callback: types.CallbackQuery):
    if callback.data not in ["btn_close", "btn_story", "btn_back_main"]:
        await callback.answer("⏳ این بخش در حال توسعه است...", show_alert=True)

# ==========================================
# 🔥 اجرای هسته
# ==========================================
async def main():
    print("🤖 ربات تاتاروس روشن شد! آماده پاسخگویی به کلمه 'تاتاروس' در گروه‌ها...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
