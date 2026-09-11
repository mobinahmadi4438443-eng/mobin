import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🧩 کیبورد شیشه‌ای منوی اصلی (طبق چیدمان درخواستی)
# ==========================================
def main_menu_keyboard():
    b = InlineKeyboardBuilder()
    
    # اضافه کردن دکمه‌ها (از ایموجی‌های استاندارد استفاده شده است)
    b.button(text="حساب کاربری 👤", callback_data="btn_profile")
    b.button(text="بازار 🛒", callback_data="btn_market")
    
    b.button(text="داستانی 📜", callback_data="btn_story")
    b.button(text="مولتی(چند جهانی) 🌍", callback_data="btn_multi")
    
    b.button(text="اسکین 🎭", callback_data="btn_skin")
    b.button(text="ارتقا ⬆️", callback_data="btn_upgrade")
    
    b.button(text="ماموریت ها 🎯", callback_data="btn_missions") # این دکمه تکی و تمام‌عرض است
    
    b.button(text="جنگ ها ⚔️", callback_data="btn_wars")
    b.button(text="بازار سیاه 🧳", callback_data="btn_blackmarket")
    
    b.button(text="فروشگاه 🏪", callback_data="btn_shop")
    b.button(text="لیدربرد 🏆", callback_data="btn_leaderboard")
    
    b.button(text="کلن 🛡", callback_data="btn_clan")
    b.button(text="اخبار 📰", callback_data="btn_news")
    
    b.button(text="راهنما 📖", callback_data="btn_help")
    b.button(text="بستن منو ❌", callback_data="btn_close")

    # چیدمان دقیق دکمه‌ها: 2تا 2تا 2تا 1دونه 2تا 2تا 2تا 2تا
    b.adjust(2, 2, 2, 1, 2, 2, 2, 2)
    return b.as_markup()

# ==========================================
# 🚀 هندلر گروه: ریپلای با شنیدن کلمه کلیدی
# ==========================================
# هر زمان کسی در گروه کلمه "امپراطوری ها" را بفرستد، این تابع اجرا می‌شود
@dp.message(F.text.contains("امپراطوری ها"))
async def trigger_empire_menu(message: types.Message):
    # مطمئن می‌شویم که این اتفاق فقط در گروه‌ها بیفتد
    if message.chat.type in ["group", "supergroup"]:
        
        # استفاده از تگ <tg-emoji> برای نمایش ایموجی‌های متحرک پرمیوم در متن
        text = (
            '<tg-emoji emoji-id="5282974228377789040">👑</tg-emoji> <b>منوی اصلی بازی امپراطوری ها</b>\n\n'
            '<tg-emoji emoji-id="5019617635629794161">👇</tg-emoji> بخش مورد نظر خود را انتخاب کنید:'
        )
        
        # ربات روی پیام کاربر ریپلای می‌کند
        await message.reply(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای
# ==========================================
# هندلر مخصوص دکمه "بستن منو"
@dp.callback_query(F.data == "btn_close")
async def close_menu(callback: types.CallbackQuery):
    # پاک کردن پیام منو برای خلوت شدن گروه
    await callback.message.delete()
    await callback.answer("منو با موفقیت بسته شد.", show_alert=False)

# هندلر موقت برای بقیه دکمه‌ها تا خطا ندهند
@dp.callback_query(F.data.startswith("btn_"))
async def handle_other_buttons(callback: types.CallbackQuery):
    # به جز دکمه بستن، بقیه دکمه‌ها این پیام پاپ‌آپ را نشان می‌دهند
    if callback.data != "btn_close":
        await callback.answer("⏳ این بخش به زودی به بازی اضافه خواهد شد...", show_alert=True)

# ==========================================
# 🔥 اجرای هسته ربات
# ==========================================
async def main():
    print("🤖 ربات با موفقیت روشن شد و منتظر شنیدن 'امپراطوری ها' در گروه‌هاست...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
