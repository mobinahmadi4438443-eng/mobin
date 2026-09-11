import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🧩 سیستم مدیریت ایموجی‌ها با دیکشنری
# ==========================================
# لیست آیدی‌های متحرک به همراه ایموجی جایگزین (Fallback)
EMOJI_IDS_TUPLE = [
    ("profile", "5987865893084861885", "👤"),
    ("market", "5258024802010026053", "🛒"),
    ("story", "5364052602357044385", "📜"),
    ("multi", "5361741454685256344", "🌍"),
    ("skin", "5987973065403797894", "🎭"),
    ("upgrade", "5375338737028841420", "⬆️"),
    ("missions", "5282996373229167849", "🎯"),
    ("wars", "5453991094435997597", "⚔️"),
    ("blackmarket", "5296387887984580731", "🧳"),
    ("shop", "5406683434124859552", "🏪"),
    ("leaderboard", "5415655814079723871", "🏆"),
    ("clan", "5978687277390371946", "🛡"),
    ("news", "5443038326535759644", "📰"),
    ("help", "5282843764451195532", "📖"),
    ("close", "5210952531676504517", "❌")
]

# ساخت دیکشنری خودکار با فرمت HTML (تگ tg-emoji) طبق ایده شما
emojis = {
    k: f'<tg-emoji emoji-id="{e_id}">{fallback}</tg-emoji>'
    for k, e_id, fallback in EMOJI_IDS_TUPLE
}

# ==========================================
# 🎛 کیبورد شیشه‌ای منوی اصلی
# ==========================================
def main_menu_keyboard():
    b = InlineKeyboardBuilder()
    
    # فراخوانی ایموجی‌ها از دیکشنری و قرار دادن در دکمه‌ها
    b.button(text=f"حساب کاربری {emojis['profile']}", callback_data="btn_profile")
    b.button(text=f"بازار {emojis['market']}", callback_data="btn_market")
    
    b.button(text=f"داستانی {emojis['story']}", callback_data="btn_story")
    b.button(text=f"مولتی(چند جهانی) {emojis['multi']}", callback_data="btn_multi")
    
    b.button(text=f"اسکین {emojis['skin']}", callback_data="btn_skin")
    b.button(text=f"ارتقا {emojis['upgrade']}", callback_data="btn_upgrade")
    
    b.button(text=f"ماموریت ها {emojis['missions']}", callback_data="btn_missions")
    
    b.button(text=f"{emojis['wars']} جنگ ها {emojis['wars']}", callback_data="btn_wars")
    b.button(text=f"بازار سیاه {emojis['blackmarket']}", callback_data="btn_blackmarket")
    
    b.button(text=f"فروشگاه {emojis['shop']}", callback_data="btn_shop")
    b.button(text=f"لیدربرد {emojis['leaderboard']}", callback_data="btn_leaderboard")
    
    b.button(text=f"کلن {emojis['clan']}", callback_data="btn_clan")
    b.button(text=f"اخبار {emojis['news']}", callback_data="btn_news")
    
    b.button(text=f"راهنما {emojis['help']}", callback_data="btn_help")
    b.button(text=f"بستن منو {emojis['close']}", callback_data="btn_close")

    # چیدمان: 2, 2, 2, 1, 2, 2, 2, 2
    b.adjust(2, 2, 2, 1, 2, 2, 2, 2)
    return b.as_markup()

# ==========================================
# 🚀 هندلرها
# ==========================================
@dp.message(F.text.contains("امپراطوری ها"))
async def trigger_empire_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        # در متن پیام، این تگ‌های HTML به زیبایی تبدیل به ایموجی متحرک می‌شوند
        text = (
            f'{emojis["close"]} <b>منوی اصلی بازی امپراطوری ها</b>\n\n'
            f'{emojis["missions"]} بخش مورد نظر خود را انتخاب کنید:'
        )
        
        await message.reply(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "btn_close")
async def close_menu(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query(F.data.startswith("btn_"))
async def handle_other_buttons(callback: types.CallbackQuery):
    if callback.data != "btn_close":
        await callback.answer("⏳ در حال توسعه...", show_alert=True)

# ==========================================
# 🔥 اجرا
# ==========================================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
