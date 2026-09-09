import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه و متغیرها
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789)) # آیدی عددی خودت

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = "multiverse.db"

# ==========================================
# 🗄 مدیریت دیتابیس
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
# 🧩 کیبوردهای شیشه‌ای (تماماً Inline)
# ==========================================
def main_menu_keyboard(is_admin=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="🌌 دروازه دنیاها", callback_data="menu_worlds")
    builder.button(text="🏰 امپراتوری من", callback_data="menu_empire")
    builder.button(text="🎒 دارایی و انبار", callback_data="menu_inventory")
    builder.button(text="🏦 بانک و بازار", callback_data="menu_bank")
    builder.button(text="⚔️ ارتش و جنگ‌افزار", callback_data="menu_army")
    
    # چیدمان دکمه‌ها: ردیف اول 2تا، ردیف دوم 2تا، ردیف سوم 1 دونه
    sizes = [2, 2, 1]
    
    if is_admin:
        builder.button(text="💻 پنل مدیریت (Admin)", callback_data="menu_admin")
        sizes.append(1) # اضافه کردن یک ردیف برای دکمه ادمین
        
    builder.adjust(*sizes)
    return builder.as_markup()

def worlds_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💻 دنیای سایبری", callback_data="go_cyber")
    builder.button(text="🐉 دنیای فانتزی", callback_data="go_fantasy")
    builder.button(text="🚀 دنیای فضایی", callback_data="go_space")
    builder.button(text="☢️ آخرالزمان", callback_data="go_apocalypse")
    builder.button(text="🔙 بازگشت به مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def inventory_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🧳 قاچاق به بازار سیاه", callback_data="action_smuggle")
    builder.button(text="🔄 صرافی چندجهانی", callback_data="action_exchange")
    builder.button(text="🔙 بازگشت به مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 آمار ربات", callback_data="admin_stats")
    builder.button(text="💰 تزریق پول به اقتصاد", callback_data="admin_inject")
    builder.button(text="🔙 بازگشت به مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def back_to_main_keyboard():
    # یک کیبورد ساده فقط با دکمه بازگشت برای بخش‌های در حال ساخت
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به مرکز فرماندهی", callback_data="menu_main")
    return builder.as_markup()

def back_to_worlds_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به لیست دنیاها", callback_data="menu_worlds")
    builder.button(text="🏠 مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(1, 1)
    return builder.as_markup()

# ==========================================
# 🚀 هندلرهای دستورات (Commands)
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # فقط در پی‌وی کار کند (جلوگیری از شلوغی گروه)
    if message.chat.type != "private":
        return
        
    await add_user(message.from_user.id, message.from_user.username)
    is_admin = (message.from_user.id == ADMIN_ID)
    
    text = (
        f"👑 سلام فرمانده **{message.from_user.full_name}**!\n"
        "به مرکز فرماندهی **امپراتوری‌های چندجهانی** خوش آمدید.\n\n"
        "سیستم‌های ناوبری آماده است. دستور چیست؟"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای (Callbacks)
# ==========================================

# --- 🏠 بازگشت به منوی اصلی ---
@dp.callback_query(F.data == "menu_main")
async def show_main_menu(callback: types.CallbackQuery):
    is_admin = (callback.from_user.id == ADMIN_ID)
    text = (
        f"👑 فرمانده **{callback.from_user.full_name}**، شما در مرکز فرماندهی هستید.\n"
        "بخش مورد نظر را انتخاب کنید:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="Markdown")
    await callback.answer()

# --- 🌌 دروازه دنیاها ---
@dp.callback_query(F.data == "menu_worlds")
async def show_worlds_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    current_world = user[3]
    text = (
        "🌌 **سیستم ناوبری چندجهانی**\n\n"
        f"📍 موقعیت فعلی شما: **{current_world.upper()}**\n\n"
        "کوردینات (مختصات) مقصد را انتخاب کنید:"
    )
    await callback.message.edit_text(text, reply_markup=worlds_keyboard(), parse_mode="Markdown")
    await callback.answer()

# --- 🎒 انبار و دارایی ---
@dp.callback_query(F.data == "menu_inventory")
async def show_inventory_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    balance = user[2]
    level = user[4]
    text = (
        "🎒 **انبار شخصی**\n\n"
        f"⚜️ سطح کاربری: {level}\n"
        f"💰 موجودی کل: **{balance:,}** سکه\n\n"
        "گزینه مورد نظر را انتخاب کنید:"
    )
    await callback.message.edit_text(text, reply_markup=inventory_keyboard(), parse_mode="Markdown")
    await callback.answer()

# --- 💻 پنل مدیریت ---
@dp.callback_query(F.data == "menu_admin")
async def show_admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
    
    text = "💻 **پنل فرماندهی کل (Super Admin)**\n\nسیستم‌های نظارتی آماده به کار هستند."
    await callback.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="Markdown")
    await callback.answer()

# --- ⏳ بخش‌های در حال ساخت ---
@dp.callback_query(F.data.in_({"menu_empire", "menu_bank", "menu_army"}))
async def show_coming_soon(callback: types.CallbackQuery):
    section_name = ""
    if callback.data == "menu_empire": section_name = "🏰 امپراتوری"
    elif callback.data == "menu_bank": section_name = "🏦 بانک مرکزی"
    elif callback.data == "menu_army": section_name = "⚔️ ارتش و جنگ‌افزار"

    text = f"⚠️ بخش **{section_name}** در حال ساخت است و در آپدیت بعدی فعال می‌شود..."
    await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="Markdown")
    await callback.answer("در حال توسعه...", show_alert=False)

# --- 🚀 عملیات سفر بین دنیاها ---
@dp.callback_query(F.data.startswith("go_"))
async def process_world_travel(callback: types.CallbackQuery):
    destination = callback.data.split("_")[1] # کلمه بعد از go_ را می‌گیرد
    
    # آپدیت دیتابیس
    await update_world(callback.from_user.id, destination)
    
    text = (
        "✨ **انتقال با موفقیت انجام شد!**\n\n"
        f"شما اکنون در **دنیای {destination.upper()}** فرود آمدید."
    )
    await callback.message.edit_text(text, reply_markup=back_to_worlds_keyboard(), parse_mode="Markdown")
    await callback.answer(f"به دنیای {destination} خوش آمدید!", show_alert=False)

# ==========================================
# 🔥 اجرای هسته ربات
# ==========================================
async def main():
    await init_db()
    print("🤖 سیستم 100% Inline شد. ربات آماده کار است...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
