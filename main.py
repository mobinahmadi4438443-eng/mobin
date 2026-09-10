import asyncio
import logging
import os
import random
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
# 🎮 حافظه موقت برای راید (نقشه زنده)
# ==========================================
# این دیکشنری وضعیت نقشه هر بازیکن را در لحظه ذخیره می‌کند
active_raids = {}

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
                current_world TEXT DEFAULT 'apocalypse',
                level INTEGER DEFAULT 1,
                fuel INTEGER DEFAULT 0,
                mana INTEGER DEFAULT 0,
                scrap INTEGER DEFAULT 0
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

async def save_raid_loot(user_id, scrap_amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET scrap = scrap + ? WHERE user_id = ?', (scrap_amount, user_id))
        await db.commit()

# ==========================================
# 🧩 کیبوردهای منوی اصلی
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
    builder.button(text="☢️ آخرالزمان (ورود رایگان)", callback_data="intel_apocalypse")
    builder.button(text="💻 سایبری (سطح 3)", callback_data="intel_cyber")
    builder.button(text="🔙 مرکز فرماندهی", callback_data="menu_main")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

# ==========================================
# 🗺 سیستم ساخت و رندر نقشه (مینی‌گیم آخرالزمان)
# ==========================================
def start_new_raid(user_id):
    # ساخت نقشه 5x5
    # 0: خالی 🟩, 1: جعبه لوت 📦, 2: زامبی 🧟‍♂️, 3: نقطه استخراج 🚁
    grid = [[0 for _ in range(5)] for _ in range(5)]
    
    # قرار دادن 4 جعبه لوت تصادفی
    for _ in range(4):
        grid[random.randint(0, 4)][random.randint(0, 4)] = 1
        
    # قرار دادن 3 زامبی تصادفی
    for _ in range(3):
        grid[random.randint(0, 4)][random.randint(0, 4)] = 2
        
    # قرار دادن هلیکوپتر استخراج (حوالی لبه‌ها)
    grid[4][random.randint(0, 4)] = 3
    
    # نقطه شروع بازیکن همیشه 0,0 است، پس آنجا را خالی می‌کنیم
    grid[0][0] = 0

    active_raids[user_id] = {
        "grid": grid,
        "pos": [0, 0], # x, y
        "hp": 100,
        "loot": 0,
        "status": "playing", # playing, dead, escaped
        "msg": "وارد خرابه شدی... مراقب باش!"
    }

def render_map(user_id):
    state = active_raids[user_id]
    grid = state["grid"]
    px, py = state["pos"]
    
    map_str = ""
    for y in range(5):
        for x in range(5):
            if x == px and y == py:
                map_str += "👤"
            # سیستم مه جنگ (فقط شعاع 1 خانه اطراف دیده می‌شود)
            elif abs(x - px) <= 1 and abs(y - py) <= 1:
                val = grid[y][x]
                if val == 0: map_str += "🟩"
                elif val == 1: map_str += "📦"
                elif val == 2: map_str += "🧟‍♂️"
                elif val == 3: map_str += "🚁"
            else:
                map_str += "⬛️"
        map_str += "\n"
    
    return map_str

def raid_controls_keyboard():
    b = InlineKeyboardBuilder()
    b.button(text=" ", callback_data="ignore")
    b.button(text="⬆️", callback_data="move_up")
    b.button(text=" ", callback_data="ignore")
    
    b.button(text="⬅️", callback_data="move_left")
    b.button(text="🔍", callback_data="ignore")
    b.button(text="➡️", callback_data="move_right")
    
    b.button(text=" ", callback_data="ignore")
    b.button(text="⬇️", callback_data="move_down")
    b.button(text=" ", callback_data="ignore")
    
    b.button(text="🏃‍♂️ فرار با دست خالی", callback_data="flee_raid")
    b.adjust(3, 3, 3, 1)
    return b.as_markup()

# ==========================================
# 🚀 هندلرهای پایه
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

@dp.callback_query(F.data == "menu_main")
async def show_main_menu(callback: types.CallbackQuery):
    is_admin = (callback.from_user.id == ADMIN_ID)
    text = "👑 شما در مرکز فرماندهی هستید. بخش مورد نظر را انتخاب کنید:"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin), parse_mode="HTML")

@dp.callback_query(F.data == "menu_worlds")
async def show_worlds_menu(callback: types.CallbackQuery):
    text = "🌌 <b>دروازه دنیاها (مولتی‌ورس)</b>\n\nبرای اعزام روی دنیای مورد نظر کلیک کنید:"
    await callback.message.edit_text(text, reply_markup=worlds_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "intel_apocalypse")
async def show_apocalypse_intel(callback: types.CallbackQuery):
    text = (
        "☢️ <b>گیت ورودی: دنیای آخرالزمان</b>\n\n"
        "شما در حال اعزام به یک منطقه رادیواکتیو و پر از زامبی هستید.\n"
        "هدف: لوت کردن آهن‌قراضه (Scrap) و رسیدن به هلیکوپتر نجات (🚁).\n"
        "هشدار: اگر بمیرید، تمام لوت‌های این سفر نابود می‌شود!\n\n"
        "آیا آماده اعزام هستید؟"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🪂 اعزام به نقشه (شروع راید)", callback_data="start_raid")
    b.button(text="🔙 انصراف", callback_data="menu_worlds")
    b.adjust(1, 1)
    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")

# ==========================================
# 🎮 هندلرهای مینی‌گیم نقشه (راید)
# ==========================================
@dp.callback_query(F.data == "start_raid")
async def process_start_raid(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    start_new_raid(user_id) # ساخت نقشه اختصاصی در رم
    
    state = active_raids[user_id]
    map_visual = render_map(user_id)
    
    text = (
        f"📻 <b>رادار بقا - متصل شد</b>\n"
        f"<i>{state['msg']}</i>\n\n"
        f"❤️ سلامتی: {state['hp']}/100\n"
        f"🎒 لوت کوله‌پشتی: {state['loot']} آهن‌قراضه\n\n"
        f"{map_visual}"
    )
    await callback.message.edit_text(text, reply_markup=raid_controls_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("move_"))
async def process_movement(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in active_raids:
        return await callback.answer("بازی شما منقضی شده است!", show_alert=True)
        
    state = active_raids[user_id]
    if state["status"] != "playing":
        return await callback.answer("این راید تمام شده است!", show_alert=True)

    direction = callback.data.split("_")[1]
    px, py = state["pos"]
    
    # محاسبه موقعیت جدید
    nx, ny = px, py
    if direction == "up" and py > 0: ny -= 1
    elif direction == "down" and py < 4: ny += 1
    elif direction == "left" and px > 0: nx -= 1
    elif direction == "right" and px < 4: nx += 1
    else:
        return await callback.answer("دیوار! نمی‌توانی از نقشه خارج شوی.", show_alert=False)

    # حرکت انجام شد، بررسی برخوردها
    state["pos"] = [nx, ny]
    cell_value = state["grid"][ny][nx]
    
    if cell_value == 1: # جعبه لوت
        found = random.randint(10, 35)
        state["loot"] += found
        state["grid"][ny][nx] = 0 # جعبه خالی شد
        state["msg"] = f"📦 عالی! {found} آهن‌قراضه پیدا کردی."
        
    elif cell_value == 2: # زامبی
        dmg = random.randint(20, 45)
        state["hp"] -= dmg
        state["grid"][ny][nx] = 0 # زامبی کشته شد
        if state["hp"] <= 0:
            state["hp"] = 0
            state["status"] = "dead"
            state["msg"] = "💀 تو توسط زامبی‌ها تیکه پاره شدی... تمام لوت‌ها از دست رفت!"
        else:
            state["msg"] = f"🩸 یک زامبی به تو حمله کرد! {dmg} دمیج خوردی."
            
    elif cell_value == 3: # هلیکوپتر (خروج موفق)
        state["status"] = "escaped"
        state["msg"] = f"🚁 استخراج موفقیت آمیز! {state['loot']} آهن‌قراضه به انبارت اضافه شد."
        await save_raid_loot(user_id, state['loot'])
        
    else:
        state["msg"] = "پایگاه امن..."

    # آپدیت صفحه نمایش
    map_visual = render_map(user_id)
    text = (
        f"📻 <b>رادار بقا - متصل شد</b>\n"
        f"<i>{state['msg']}</i>\n\n"
        f"❤️ سلامتی: {state['hp']}/100\n"
        f"🎒 لوت کوله‌پشتی: {state['loot']} آهن‌قراضه\n\n"
        f"{map_visual}"
    )

    # اگر بازی تمام شده دکمه بازگشت نشان بده
    if state["status"] != "playing":
        b = InlineKeyboardBuilder()
        b.button(text="🏠 بازگشت به پایگاه", callback_data="menu_main")
        await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")
        del active_raids[user_id] # پاک کردن از رم
    else:
        await callback.message.edit_text(text, reply_markup=raid_controls_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "flee_raid")
async def process_flee(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in active_raids:
        del active_raids[user_id]
    text = "🏃‍♂️ از ترس فرار کردی... تمام لوت‌هایی که جمع کرده بودی را در راه انداختی!"
    b = InlineKeyboardBuilder()
    b.button(text="🏠 بازگشت به پایگاه", callback_data="menu_main")
    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    await callback.answer() # برای دکمه‌های خالی کیبورد حرکت

# ==========================================
# ⚙️ هندلرهای در حال ساخت و انبار
# ==========================================
@dp.callback_query(F.data == "menu_inventory")
async def show_inventory_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    balance, level, scrap = user[2], user[4], user[7]
    text = (
        "🎒 <b>انبار شخصی</b>\n\n"
        f"⚜️ سطح: {level}\n"
        f"💰 سکه: {balance:,}\n"
        f"⚙️ آهن‌قراضه: {scrap}\n\n"
    )
    b = InlineKeyboardBuilder()
    b.button(text="🔙 بازگشت", callback_data="menu_main")
    await callback.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.in_({"menu_empire", "menu_bank", "menu_army"}))
async def show_coming_soon(callback: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.button(text="🔙 بازگشت", callback_data="menu_main")
    await callback.message.edit_text("⚠️ این بخش در آپدیت بعدی فعال می‌شود.", reply_markup=b.as_markup())

# ==========================================
# 🔥 اجرای هسته ربات
# ==========================================
async def main():
    await init_db()
    print("🤖 سیستم رادار زنده متصل شد. ربات آماده کار است...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
