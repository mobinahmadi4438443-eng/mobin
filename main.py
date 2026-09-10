import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = "multiverse.db"

# ==========================================
# 🗄 مدیریت دیتابیس پیشرفته
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # اضافه شدن سوخت و مانا به دیتابیس
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 1000,
                current_world TEXT DEFAULT 'apocalypse',
                level INTEGER DEFAULT 1,
                fuel INTEGER DEFAULT 0,
                mana INTEGER DEFAULT 0
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

async def update_world(user_id, world_name, fuel_cost=0, mana_cost=0):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            UPDATE users 
            SET current_world = ?, fuel = fuel - ?, mana = mana - ? 
            WHERE user_id = ?
        ''', (world_name, fuel_cost, mana_cost, user_id))
        await db.commit()

async def buy_resource(user_id, resource_type, amount, cost):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE users SET balance = balance - ?, {resource_type} = {resource_type} + ? WHERE user_id = ?', (cost, amount, user_id))
        await db.commit()

# ==========================================
# 🧩 کیبوردهای شیشه‌ای
# ==========================================
def main_menu_keyboard(is_admin=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="🌌 دروازه دنیاها", callback_data="menu_worlds")
    builder.button(text="🏰 امپراتوری من", callback_data="menu_empire")
    builder.button(text="🎒 دارایی و انبار", callback_data="menu_inventory")
    builder.button(text="🏦 بانک و بازار", callback_data="menu_bank")
    builder.button(text="⚔️ ارتش و جنگ‌افزار", callback_data="menu_army")
    sizes = [2, 2, 1]
    if is_admin:
        builder.button(text="💻 پنل مدیریت", callback_data="menu_admin")
        sizes.append(1)
    builder.adjust(*sizes)
    return builder.as_markup()

def worlds_keyboard():
    builder = InlineKeyboardBuilder()
    # الان دکمه‌ها به جای go_ به intel_ (اطلاعات) وصل هستند
    builder.button(text="💻 سایبری (سطح 3)", callback_data="intel_cyber")
    builder.button(text="🐉 فانتزی (سطح 2)", callback_data="intel_fantasy")
    builder.button(text="🚀 فضایی (سطح 5)", callback_data="intel_space")
    builder.button(text="☢️ آخرالزمان (رایگان)", callback_data="intel_apocalypse")
    builder.button(text="🔙 بازگشت به مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def intel_keyboard(world):
    builder = InlineKeyboardBuilder()
    builder.button(text="✈️ پرش ابعادی (سفر)", callback_data=f"travel_{world}")
    if world in ["cyber", "space"]:
        builder.button(text="⛽️ خرید 10 لیتر سوخت (100 سکه)", callback_data="buy_fuel_10")
    elif world == "fantasy":
        builder.button(text="🔮 خرید 5 کریستال مانا (150 سکه)", callback_data="buy_mana_5")
        
    builder.button(text="🔙 بازگشت به لیست دنیاها", callback_data="menu_worlds")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

def back_to_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به مرکز", callback_data="menu_main")
    return builder.as_markup()

# ==========================================
# 🚀 هندلرهای پیام و دستورات
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)
    is_admin = (message.from_user.id == ADMIN_ID)
    
    text = (
        f"👑 سلام فرمانده <b>{message.from_user.full_name}</b>!\n"
        f"به مرکز فرماندهی <b>امپراتوری‌های چندجهانی</b> خوش آمدید.\n\n"
        "سیستم‌های ناوبری آماده است. دستور چیست؟"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="HTML")

# ==========================================
# 🎛 هندلرهای ناوبری اصلی
# ==========================================
@dp.callback_query(F.data == "menu_main")
async def show_main_menu(callback: types.CallbackQuery):
    is_admin = (callback.from_user.id == ADMIN_ID)
    text = f"👑 فرمانده <b>{callback.from_user.full_name}</b>، شما در مرکز هستید. بخش مورد نظر را انتخاب کنید:"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "menu_worlds")
async def show_worlds_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    current_world = user[3]
    text = (
        "🌌 <b>دروازه دنیاها (مولتی‌ورس)</b>\n\n"
        f"📍 موقعیت فعلی شما: <b>{current_world.upper()}</b>\n\n"
        "برای مشاهده وضعیت و سفر به هر دنیا، روی آن کلیک کنید:"
    )
    await callback.message.edit_text(text, reply_markup=worlds_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "menu_inventory")
async def show_inventory_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    balance, current_world, level, fuel, mana = user[2], user[3], user[4], user[5], user[6]
    
    text = (
        "🎒 <b>انبار شخصی</b>\n\n"
        f"⚜️ سطح کاربری: <b>{level}</b>\n"
        f"📍 دنیای فعلی: <b>{current_world.upper()}</b>\n\n"
        "<b>دارایی‌ها:</b>\n"
        f"💰 سکه: {balance:,}\n"
        f"⛽️ سوخت: {fuel} لیتر\n"
        f"🔮 مانا: {mana} کریستال"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main_keyboard(), parse_mode="HTML")
    await callback.answer()

# ==========================================
# 🌌 هندلرهای اطلاعات دنیاها (Intel Board)
# ==========================================
@dp.callback_query(F.data.startswith("intel_"))
async def show_world_intel(callback: types.CallbackQuery):
    world = callback.data.split("_")[1]
    
    intel_data = {
        "apocalypse": {"name": "آخرالزمان", "level": 1, "cost": "رایگان", "status": "بقا و غارت"},
        "fantasy": {"name": "فانتزی", "level": 2, "cost": "5 کریستال مانا", "status": "جادوی باستانی بیدار شده"},
        "cyber": {"name": "سایبری", "level": 3, "cost": "10 لیتر سوخت", "status": "تورم قطعات الکترونیکی"},
        "space": {"name": "فضایی", "level": 5, "cost": "30 لیتر سوخت", "status": "حمله دزدان فضایی"}
    }
    
    data = intel_data.get(world)
    text = (
        f"🖥 <b>گیت ورودی: دنیای {data['name']}</b>\n\n"
        f"⚜️ <b>پیش‌نیاز سطح:</b> {data['level']}\n"
        f"🎟 <b>هزینه سفر:</b> {data['cost']}\n"
        f"📊 <b>وضعیت زنده:</b> {data['status']}\n\n"
        "آیا برای پرش ابعادی آماده‌اید؟"
    )
    await callback.message.edit_text(text, reply_markup=intel_keyboard(world), parse_mode="HTML")
    await callback.answer()

# ==========================================
# ✈️ هندلرهای سفر بین دنیاها و خرید منابع
# ==========================================
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_resource(callback: types.CallbackQuery):
    action = callback.data.split("_")
    res_type = action[1]
    amount = int(action[2])
    
    user = await get_user(callback.from_user.id)
    balance = user[2]
    
    cost = 100 if res_type == "fuel" else 150
    
    if balance < cost:
        return await callback.answer("⛔️ سکه کافی ندارید!", show_alert=True)
        
    await buy_resource(callback.from_user.id, res_type, amount, cost)
    await callback.answer(f"✅ {amount} {res_type} خریداری شد!", show_alert=True)

@dp.callback_query(F.data.startswith("travel_"))
async def process_world_travel(callback: types.CallbackQuery):
    world = callback.data.split("_")[1]
    user = await get_user(callback.from_user.id)
    current_world, level, fuel, mana = user[3], user[4], user[5], user[6]
    
    if current_world == world:
        return await callback.answer("شما در حال حاضر در این دنیا هستید!", show_alert=True)
        
    # چک کردن پیش‌نیازها
    fuel_cost, mana_cost = 0, 0
    if world == "cyber":
        if level < 3: return await callback.answer("⛔️ نیاز به سطح 3 دارید!", show_alert=True)
        if fuel < 10: return await callback.answer("⛔️ سوخت کافی نیست!", show_alert=True)
        fuel_cost = 10
    elif world == "fantasy":
        if level < 2: return await callback.answer("⛔️ نیاز به سطح 2 دارید!", show_alert=True)
        if mana < 5: return await callback.answer("⛔️ کریستال مانا کافی نیست!", show_alert=True)
        mana_cost = 5
    elif world == "space":
        if level < 5: return await callback.answer("⛔️ نیاز به سطح 5 دارید!", show_alert=True)
        if fuel < 30: return await callback.answer("⛔️ سوخت کافی نیست!", show_alert=True)
        fuel_cost = 30
        
    # کم کردن منابع و آپدیت دنیا
    await update_world(callback.from_user.id, world, fuel_cost, mana_cost)
    
    text = (
        "✨ <b>پرش ابعادی با موفقیت انجام شد!</b>\n\n"
        f"شما اکنون در <b>دنیای {world.upper()}</b> فرود آمدید و منابع سفر کسر شد."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به لیست دنیاها", callback_data="menu_worlds")
    builder.button(text="🏠 مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer("سفر با موفقیت انجام شد!")

# ==========================================
# 🔥 اجرای هسته ربات
# ==========================================
async def main():
    await init_db()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
