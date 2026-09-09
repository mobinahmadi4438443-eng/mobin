import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه و متغیرها
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار_اگر_در_ریلوی_نیست")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789)) # آیدی عددی خودت

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# نام دیتابیس
DB_NAME = "multiverse.db"

# ==========================================
# 🗄 مدیریت دیتابیس (حرفه‌ای و ناهمگام)
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 1000,
                current_world TEXT DEFAULT 'cyber',
                level INTEGER DEFAULT 1
            )
        ''')
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(user_id, username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        await db.commit()

async def update_world(user_id, world_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET current_world = ? WHERE user_id = ?', (world_name, user_id))
        await db.commit()

# ==========================================
# 🎛 کیبوردهای اصلی (PV)
# ==========================================
def main_reply_keyboard(is_admin=False):
    kb = [
        [KeyboardButton(text="🌌 دروازه دنیاها"), KeyboardButton(text="🏰 امپراتوری من")],
        [KeyboardButton(text="🎒 دارایی و انبار"), KeyboardButton(text="🏦 بانک و بازار")],
        [KeyboardButton(text="⚔️ ارتش و جنگ‌افزار")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="💻 پنل مدیریت (Admin)")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="فرمانده، دستور چیست؟")

# ==========================================
# 🧩 کیبوردهای شیشه‌ای (Inline) با دکمه بازگشت
# ==========================================
def worlds_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💻 دنیای سایبری", callback_data="go_cyber")
    builder.button(text="🐉 دنیای فانتزی", callback_data="go_fantasy")
    builder.button(text="🚀 دنیای فضایی", callback_data="go_space")
    builder.button(text="☢️ آخرالزمان", callback_data="go_apocalypse")
    builder.button(text="🔙 بستن پنل", callback_data="close_panel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def inventory_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🧳 قاچاق به بازار سیاه", callback_data="action_smuggle")
    builder.button(text="🔄 صرافی چندجهانی", callback_data="action_exchange")
    builder.button(text="🔙 بستن پنل", callback_data="close_panel")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

def admin_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 آمار ربات", callback_data="admin_stats")
    builder.button(text="💰 تزریق پول به اقتصاد", callback_data="admin_inject")
    builder.button(text="🔙 بستن پنل", callback_data="close_panel")
    builder.adjust(2, 1)
    return builder.as_markup()

def back_to_worlds_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به منوی دنیاها", callback_data="menu_worlds")
    return builder.as_markup()

# ==========================================
# 🚀 هندلرهای پیام‌ها (Commands & Messages)
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)
    is_admin = (message.from_user.id == ADMIN_ID)
    
    welcome_text = (
        f"👑 سلام فرمانده {message.from_user.full_name}!\n"
        "به ربات امپراتوری‌های چندجهانی خوش آمدید.\n\n"
        "شما اکنون در پایگاه اصلی هستید. از منوی زیر برای مدیریت امپراتوری خود استفاده کنید."
    )
    await message.answer(welcome_text, reply_markup=main_reply_keyboard(is_admin))

@dp.message(F.text == "🌌 دروازه دنیاها")
async def show_worlds(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("لطفا ابتدا ربات را /start کنید.")
    
    current_world = user[3] # Index 3 is current_world in our tuple
    text = (
        "🌌 **سیستم ناوبری چندجهانی فعال شد.**\n\n"
        f"📍 دنیای فعلی شما: **{current_world.upper()}**\n\n"
        "برای سفر به دنیای جدید، مقصد را انتخاب کنید:"
    )
    await message.answer(text, reply_markup=worlds_inline_keyboard(), parse_mode="Markdown")

@dp.message(F.text == "🎒 دارایی و انبار")
async def show_inventory(message: types.Message):
    user = await get_user(message.from_user.id)
    balance = user[2]
    level = user[4]
    
    text = (
        "🎒 **انبار شخصی شما**\n\n"
        f"⚜️ سطح کاربری: {level}\n"
        f"💰 موجودی کل: {balance:,} سکه\n\n"
        "چه عملیاتی می‌خواهید انجام دهید؟"
    )
    await message.answer(text, reply_markup=inventory_inline_keyboard())

@dp.message(F.text == "💻 پنل مدیریت (Admin)")
async def show_admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ شما به این بخش دسترسی ندارید.")
    
    text = "💻 **پنل فرماندهی کل (Super Admin)**\n\nبه پنل کنترل مولتی‌ورس خوش آمدید قربان!"
    await message.answer(text, reply_markup=admin_inline_keyboard())

@dp.message(F.text.in_({"🏰 امپراتوری من", "🏦 بانک و بازار", "⚔️ ارتش و جنگ‌افزار"}))
async def coming_soon(message: types.Message):
    await message.answer("⚠️ این بخش در آپدیت بعدی پایگاه در دسترس قرار می‌گیرد. در حال ساخت و توسعه...")

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای (Callbacks)
# ==========================================
@dp.callback_query(F.data.startswith("go_"))
async def travel_world(callback: types.CallbackQuery):
    destination = callback.data.split("_")[1] # e.g., 'cyber' from 'go_cyber'
    
    # آپدیت دیتابیس
    await update_world(callback.from_user.id, destination)
    
    # ویرایش پیام قبلی و قرار دادن دکمه بازگشت
    text = f"✨ انتقال با موفقیت انجام شد!\n\nشما اکنون در **دنیای {destination.upper()}** هستید."
    await callback.message.edit_text(text, reply_markup=back_to_worlds_keyboard(), parse_mode="Markdown")
    await callback.answer(f"به دنیای {destination} خوش آمدید!", show_alert=False)

@dp.callback_query(F.data == "menu_worlds")
async def back_to_worlds_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    current_world = user[3]
    text = (
        "🌌 **سیستم ناوبری چندجهانی فعال شد.**\n\n"
        f"📍 دنیای فعلی شما: **{current_world.upper()}**\n\n"
        "برای سفر به دنیای جدید، مقصد را انتخاب کنید:"
    )
    # بازگشت به لیست دنیاها
    await callback.message.edit_text(text, reply_markup=worlds_inline_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "close_panel")
async def close_inline_panel(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("پنل بسته شد.")

# ==========================================
# 🔥 روتر اجرای اصلی ربات
# ==========================================
async def main():
    await init_db()
    print("🤖 دیتابیس متصل شد. ربات در حال روشن شدن است...")
    try:
        # پاک کردن آپدیت‌های آفلاین تا ربات اسپم نشود
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())