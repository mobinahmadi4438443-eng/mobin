import asyncio
import logging
import os
import re
import random
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))
DB_NAME = "tatarus.db"
BOT_USERNAME = None  

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🗄 دیتابیس
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        await db.commit()
    
    defaults = {
        "char1_name": "زولو = ZOLLO", "char1_emoji": "5832457500821034730",
        "char2_name": "نورا = NORA",  "char2_emoji": "",
        "char3_name": "جسپر = JESPER", "char3_emoji": "",
        "char4_name": "رکس = REX",   "char4_emoji": ""
    }
    for k, v in defaults.items():
        if await get_setting(k) is None:
            await set_setting(k, v)

async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

# ==========================================
# 🧩 ایموجی و پردازشگر متن (ایمن در برابر شماره کارت و کدهای تکراری)
# ==========================================
async def get_emoji(btn_name: str, default_id: str):
    return await get_setting(f"emoji_{btn_name}", default_id)

def parse_emojis(text: str) -> str:
    # فقط اعداد 18 تا 22 رقمی را پردازش می‌کند تا تداخلی با شماره کارت‌های 16 رقمی نداشته باشد
    return re.sub(r'(?<!["\'\d])(\d{18,22})(?!["\'\d])', r'<tg-emoji emoji-id="\1">✨</tg-emoji>', text)

# ==========================================
# 📝 متون اصلی ربات
# ==========================================
MAIN_TEXT = parse_emojis("5282974228377789040 <b>منوی اصلی بازی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
GAME_MENU_TEXT = parse_emojis("5282974228377789040 <b>منوی داستانی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
CHAR_SELECTION_TEXT = parse_emojis("کاراکتر مورد نظر خودرا انتخاب کنید 5019617635629794161")
STORY_TEXT = (
    'سلام <tg-emoji emoji-id="5296480809602023717">✨</tg-emoji>\n'
    'به بازی تاتاروس خوش آمدید <tg-emoji emoji-id="5296349143084595007">✨</tg-emoji>\n\n'
    'با فشار دادن/کلیک کردن روی دکمه شروع وارد دنیای فراموش شده میشید.<tg-emoji emoji-id="5303073678890662588">✨</tg-emoji>\n\n'
    'دنیای فراموش شده جای افرادیه که در دنیای خودشون مرتکب اشتباهات زیادی شدن و تبعید شدن به دنیای فراموش شده.<tg-emoji emoji-id="5296785692150497491">✨</tg-emoji>\n\n'
    'برای اینکه بتونید از دنیای فراموش شده فرار کنید مجموعه ای از ماموریت ها و دشمن های مختلفی رو باید پشت سر بزارید.<tg-emoji emoji-id="5453991094435997597">✨</tg-emoji>\n\n'
    'باید در طول انجام ماموریت و مبارزه حواستون باشه که نیازمند هستید به منابع مختلف،\n'
    'مثل سکه، الماس و ...<tg-emoji emoji-id="5213094908608392768">✨</tg-emoji>\n\n'
    '<tg-emoji emoji-id="5395695537687123235">✨</tg-emoji> در طول مبارزات به شما مقدار قابل توجهی منابع تعلق میگیره ولی همیشه به این معنا نیست که قراره کافی باشن پس بهتره به بخش ماموریت ها هم سر بزنید<tg-emoji emoji-id="5395695537687123235">✨</tg-emoji>\n\n'
    'اولین دشمن شما دراخور هستش برای کشتن اون نیاز به\n\n'
    ' 45،000 سکه دارید <tg-emoji emoji-id="5282996373229167849">✨</tg-emoji>\n\n'
    'و 1750 XP خون لازم دارید🩸\n\n'
    'دراخور دشمن ساده ای نیست پس حواستو جمع کن تو دامش نیوفتی<tg-emoji emoji-id="5440660757194744323">✨</tg-emoji>'
)
UPGRADE_TEXT = parse_emojis("به بخش ارتقا سلاح ها خوش امدید 6021530065794244533\n\nسلاح شما : چاقو (دیفالت بازی) هستش 5830442181906667908\n\nبرای ارتقا روی دکمه چاقو کلیک کنید 5019617635629794161\n\nو برای خرید سلاح جدید روی سلاح مورد نظر کلیک نمایید 5019759554234156094")
WEAPONS = {"چاقو": "knife", "شمشیر": "sword", "کُلت": "colt", "کلاش": "ak47"}

def get_daily_reward_text():
    coins = random.randint(10, 3000)
    xp = random.randint(1, 50)
    return (
        '<tg-emoji emoji-id="5785281906459283269">✨</tg-emoji> هدیه روزانه\n\n'
        '<tg-emoji emoji-id="6034853518202903906">✨</tg-emoji> هدیه روزانه آماده است!\n\n'
        f'<tg-emoji emoji-id="6032699501909644905">✨</tg-emoji> {coins:,} سکه!\n\n'
        f'<tg-emoji emoji-id="6035017564478773073">✨</tg-emoji> {xp} XP\n\n'
        '<tg-emoji emoji-id="5019759554234156094">✨</tg-emoji> برای گرفتنش دکمه دریافت جوایز رو بزنید! <tg-emoji emoji-id="5019759554234156094">✨</tg-emoji>'
    )

# ==========================================
# 📡 ارتباط خام با تلگرام
# ==========================================
async def send_raw_api(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"): logging.error(f"Telegram API Error: {result}")
            return result

# ==========================================
# 💎 پنل مدیریت شیشه‌ای (Admin UI)
# ==========================================
class AdminSetup(StatesGroup):
    waiting_for_photo = State()
    waiting_for_text = State()
    waiting_for_emoji_btn_name = State()
    waiting_for_emoji_code = State()
    guide_text_page = State()
    guide_photo_page = State()
    waiting_for_char_names = State()

class UserBuy(StatesGroup):
    waiting_for_contact = State()
    waiting_for_receipt = State()

def get_admin_home_kb():
    b = InlineKeyboardBuilder()
    b.button(text="منو اصلی", callback_data="adm_cat_main")
    b.button(text="داستانی", callback_data="adm_cat_story")
    b.adjust(2)
    return b.as_markup()

async def get_admin_main_cat_kb():
    icon = "✅" if await get_setting("photo_main") else "❌"
    b = InlineKeyboardBuilder()
    b.button(text=f"عکس منو {icon}", callback_data="adm_req_photo_main")
    b.button(text="بازگشت", callback_data="adm_home")
    b.adjust(1)
    return b.as_markup()

async def get_admin_story_cat_kb():
    b = InlineKeyboardBuilder()
    def ic(val): return "✅" if val else "❌"
    
    b.button(text=f"اوپنینگ {ic(await get_setting('photo_story'))}", callback_data="adm_req_photo_story")
    b.button(text=f"کاراکترها {ic(await get_setting('photo_character'))}", callback_data="adm_req_photo_character")
    b.button(text=f"منو داستانی {ic(await get_setting('photo_gamemenu'))}", callback_data="adm_req_photo_gamemenu")
    b.button(text=f"منو ارتقا {ic(await get_setting('photo_upgrade'))}", callback_data="adm_req_photo_upgrade")
    b.button(text=f"جایزه روزانه {ic(await get_setting('photo_gamedaily'))}", callback_data="adm_req_photo_gamedaily")
    
    b.button(text="حیوانات 🐾", callback_data="adm_cats_pets")
    b.button(text="سلاح‌ها ⚔️", callback_data="adm_cats_weapons")
    
    b.button(text="راهنما (متن)", callback_data="adm_req_guidetext")
    b.button(text="راهنما (عکس)", callback_data="adm_req_guidephoto")
    b.button(text="اسم کاراکترها", callback_data="adm_req_charnames")
    b.button(text="متن حیوانات", callback_data="adm_req_text_pet_text")
    b.button(text="شماره کارت", callback_data="adm_req_text_bank_card_text")
    b.button(text="تغییر ایموجی‌ها ✨", callback_data="adm_req_emoji")
    
    b.button(text="بازگشت", callback_data="adm_home")
    b.adjust(2, 2, 1, 2, 2, 2, 1, 1)
    return b.as_markup()

@dp.message(F.text == "تغییرات")
async def cmd_admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.clear()
    await message.reply("⚙️ پنل مدیریت تاتاروس\n\nبخش مورد نظر را انتخاب کنید:", reply_markup=get_admin_home_kb())

@dp.callback_query(F.data.in_({"adm_home", "adm_cat_main", "adm_cat_story"}))
async def handle_admin_nav(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await state.clear()
    if callback.data == "adm_home":
        await callback.message.edit_text("⚙️ پنل مدیریت تاتاروس\n\nبخش مورد نظر را انتخاب کنید:", reply_markup=get_admin_home_kb())
    elif callback.data == "adm_cat_main":
        await callback.message.edit_text("⚙️ تنظیمات منوی اصلی:", reply_markup=await get_admin_main_cat_kb())
    elif callback.data == "adm_cat_story":
        await callback.message.edit_text("⚙️ تنظیمات بخش داستانی:", reply_markup=await get_admin_story_cat_kb())

@dp.callback_query(F.data == "adm_cats_pets")
async def admin_pets_menu(callback: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    for i in range(1, 5):
        name = await get_setting(f"char{i}_name", f"کاراکتر {i}")
        p = "✅" if await get_setting(f"photo_pet_{i}") else "❌"
        b.button(text=f"{name.split('=')[0].strip()} {p}", callback_data=f"adm_req_photo_pet_{i}")
    b.button(text="بازگشت", callback_data="adm_cat_story")
    b.adjust(2, 2, 1)
    await callback.message.edit_text("حیوان کدام کاراکتر را می‌خواهید تنظیم کنید؟", reply_markup=b.as_markup())
    
@dp.callback_query(F.data == "adm_cats_weapons")
async def admin_weapons_menu(callback: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    for w_fa, w_en in WEAPONS.items():
        p = "✅" if await get_setting(f"photo_weapon_{w_en}") else "❌"
        b.button(text=f"{w_fa} {p}", callback_data=f"adm_req_photo_weapon_{w_en}")
    b.button(text="بازگشت", callback_data="adm_cat_story")
    b.adjust(2, 2, 1)
    await callback.message.edit_text("عکس کدام سلاح را می‌خواهید تنظیم کنید؟", reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("adm_req_"))
async def handle_admin_requests(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    req = callback.data.replace("adm_req_", "")
    
    if req.startswith("photo_"):
        target = req.replace("photo_", "")
        await state.set_state(AdminSetup.waiting_for_photo)
        await state.update_data(target_menu=target, back_to="story" if target != "main" else "main")
        await callback.message.edit_text("📸 عکس مورد نظر را ارسال نمایید:")
        
    elif req.startswith("text_"):
        target = req.replace("text_", "")
        await state.set_state(AdminSetup.waiting_for_text)
        await state.update_data(target_setting=target)
        await callback.message.edit_text("لطفاً متن جدید را ارسال نمایید:")
        
    elif req == "guidetext":
        await state.set_state(AdminSetup.guide_text_page)
        await state.update_data(current_page=1)
        current_text = await get_setting("guide_text_1", "تنظیم نشده")
        await callback.message.edit_text(f"متن فعلی صفحه اول:\n\n{current_text}\n\nمتن جدید را ارسال کنید:")
        
    elif req == "guidephoto":
        await state.set_state(AdminSetup.guide_photo_page)
        await state.update_data(current_page=1)
        await callback.message.edit_text("📸 عکس راهنمای داستانی (صفحه 1) را ارسال کنید:")
        
    elif req == "charnames":
        await state.set_state(AdminSetup.waiting_for_char_names)
        await state.update_data(current_char=1)
        await callback.message.edit_text("تغییر اسم کاراکتر ها:\nاسم اولین کاراکتر را انتخاب کنید:")
        
    elif req == "emoji":
        await state.set_state(AdminSetup.waiting_for_emoji_btn_name)
        await callback.message.edit_text("نام دکمه‌ای که می‌خواهید ایموجی آن تغییر کند را ارسال کنید (مثال: شروع):")

# --- دریافت مقادیر FSM ---
@dp.message(F.photo, AdminSetup.waiting_for_photo)
async def receive_photo(message: types.Message, state: FSMContext):
    await state.update_data(temp_file_id=message.photo[-1].file_id)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="admin_confirm_photo")
    b.button(text="❌ خیر", callback_data="admin_reject")
    await message.reply("آیا عکس تایید است؟", reply_markup=b.as_markup())

@dp.message(F.text, AdminSetup.waiting_for_text)
async def receive_text_input(message: types.Message, state: FSMContext):
    await state.update_data(temp_text=message.text)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="admin_confirm_text")
    b.button(text="❌ خیر", callback_data="admin_reject")
    parsed_text = parse_emojis(message.text)
    await message.reply(f"آیا متن تایید است؟\n\n{parsed_text}", reply_markup=b.as_markup(), parse_mode="HTML")

@dp.message(F.text, AdminSetup.waiting_for_emoji_btn_name)
async def receive_emoji_btn_name(message: types.Message, state: FSMContext):
    await state.update_data(target_btn=message.text.strip())
    await state.set_state(AdminSetup.waiting_for_emoji_code)
    await message.reply(f"کد ایموجی جدید برای دکمه «{message.text.strip()}» را ارسال کنید:")

@dp.message(F.text, AdminSetup.waiting_for_emoji_code)
async def receive_emoji_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await set_setting(f"emoji_{data['target_btn']}", message.text.strip())
    kb = await get_admin_story_cat_kb()
    await message.reply(f"✅ ایموجی دکمه {data['target_btn']} تغییر یافت.\n\nپنل مدیریت:", reply_markup=kb)
    await state.clear()

# --- تایید یا رد عمومی ---
@dp.callback_query(F.data == "admin_confirm_photo")
async def confirm_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await set_setting(f"photo_{data['target_menu']}", data['temp_file_id'])
    back_to = data.get("back_to", "story")
    kb = await get_admin_main_cat_kb() if back_to == "main" else await get_admin_story_cat_kb()
    await callback.message.edit_text("✅ عکس با موفقیت تغییر یافت!\n\nپنل مدیریت:", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data == "admin_confirm_text")
async def confirm_text_action(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await set_setting(data['target_setting'], data['temp_text'])
    kb = await get_admin_story_cat_kb()
    await callback.message.edit_text("✅ متن با موفقیت تنظیم شد!\n\nپنل مدیریت:", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data == "admin_reject")
async def reject_admin(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    back_to = data.get("back_to", "story")
    kb = await get_admin_main_cat_kb() if back_to == "main" else await get_admin_story_cat_kb()
    await callback.message.edit_text("❌ عملیات لغو شد.\n\nپنل مدیریت:", reply_markup=kb)
    await state.clear()

# --- لوپ‌های راهنما و کاراکتر ---
@dp.message(AdminSetup.waiting_for_char_names)
async def receive_char_name(message: types.Message, state: FSMContext):
    raw_text = message.text
    match = re.search(r'\b(\d{18,22})\b', raw_text)
    if match:
        emoji_id = match.group(1)
        name = raw_text.replace(emoji_id, '').strip()
    else:
        emoji_id = None
        name = raw_text.strip()
        
    await state.update_data(temp_name=name, temp_emoji=emoji_id)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="char_confirm_yes")
    b.button(text="❌ خیر", callback_data="char_confirm_no")
    await message.reply(f"آیا این اسم تایید است؟\n\nنام: `{name}`", reply_markup=b.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.in_({"char_confirm_yes", "char_confirm_no"}))
async def process_char_name_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_char = data.get("current_char", 1)
    
    if callback.data == "char_confirm_yes":
        await set_setting(f"char{current_char}_name", data["temp_name"])
        if data["temp_emoji"]: await set_setting(f"char{current_char}_emoji", data["temp_emoji"])
        else: await set_setting(f"char{current_char}_emoji", "")
        await callback.message.edit_text(f"✅ اسم کاراکتر {current_char} ذخیره شد.")
    else:
        await callback.message.edit_text(f"❌ ذخیره نشد.")
        
    next_char = current_char + 1
    if next_char > 4:
        kb = await get_admin_story_cat_kb()
        await callback.message.answer("🎉 تنظیمات اسم هر ۴ کاراکتر به پایان رسید.\n\nپنل مدیریت:", reply_markup=kb)
        await state.clear()
    else:
        await state.update_data(current_char=next_char)
        await callback.message.answer(f"حالا اسم کاراکتر {next_char} را ارسال کنید:")

@dp.message(AdminSetup.guide_text_page)
async def receive_guide_text(message: types.Message, state: FSMContext):
    await state.update_data(temp_text=message.text)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="guide_txt_yes")
    b.button(text="❌ خیر", callback_data="admin_reject")
    await message.reply("آیا متن تایید است؟", reply_markup=b.as_markup())

@dp.callback_query(F.data == "guide_txt_yes")
async def confirm_guide_text(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("current_page", 1)
    await set_setting(f"guide_text_{page}", data["temp_text"])
    await set_setting("guide_pages_count", str(page)) 
    
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="guide_next_page_yes")
    b.button(text="❌ خیر", callback_data="guide_next_page_no")
    await callback.message.edit_text("صفحه بعد رو میخواهید اضافه کنید یا نه؟", reply_markup=b.as_markup())

@dp.callback_query(F.data == "guide_next_page_yes")
async def next_page_guide_text(callback: types.CallbackQuery, state: FSMContext):
    next_page = (await state.get_data()).get("current_page", 1) + 1
    await state.update_data(current_page=next_page)
    await callback.message.edit_text(f"متن جدید برای صفحه {next_page} را ارسال کنید:")

@dp.callback_query(F.data == "guide_next_page_no")
async def end_page_guide_text(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_admin_story_cat_kb()
    await callback.message.edit_text("✅ ثبت راهنمای متنی به پایان رسید.\n\nپنل مدیریت:", reply_markup=kb)
    await state.clear()

@dp.message(F.photo, AdminSetup.guide_photo_page)
async def receive_guide_photo(message: types.Message, state: FSMContext):
    await state.update_data(temp_file_id=message.photo[-1].file_id)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="guide_photo_yes")
    b.button(text="❌ خیر", callback_data="admin_reject")
    await message.reply("آیا این عکس تایید است؟", reply_markup=b.as_markup())

@dp.callback_query(F.data == "guide_photo_yes")
async def confirm_guide_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("current_page", 1)
    await set_setting(f"photo_guide_{page}", data["temp_file_id"])
    
    total_pages = int(await get_setting("guide_pages_count", "1"))
    if page < total_pages:
        next_page = page + 1
        await state.update_data(current_page=next_page)
        await callback.message.edit_text(f"✅ عکس صفحه {page} ذخیره شد.\n📸 عکس صفحه {next_page} را ارسال کنید:")
    else:
        kb = await get_admin_story_cat_kb()
        await callback.message.edit_text("✅ عکس تمامی صفحات راهنما ذخیره شد.\n\nپنل مدیریت:", reply_markup=kb)
        await state.clear()

# ==========================================
# 💰 سیستم خرید حیوان نبرد (پی‌وی ربات)
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("buypet_"):
        char_id = args[1].split("_")[1]
        await state.update_data(buy_char_id=char_id)
        await state.set_state(UserBuy.waiting_for_contact)
        
        kb = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="ارسال شماره تلفن 📱", request_contact=True)]],
            resize_keyboard=True
        )
        await message.reply("شماره تلفن خودرا تایید کنید:", reply_markup=kb)

@dp.message(F.contact, UserBuy.waiting_for_contact)
async def receive_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    remove_kb = types.ReplyKeyboardRemove()
    await message.reply("شماره دریافت شد.", reply_markup=remove_kb)
    
    card_text_raw = await get_setting("bank_card_text", "شماره کارت تنظیم نشده است.")
    char_id = (await state.get_data())["buy_char_id"]
    
    b = InlineKeyboardBuilder()
    b.button(text="واریز کردم", callback_data=f"paid_{char_id}")
    await message.answer(parse_emojis(card_text_raw), reply_markup=b.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("paid_"))
async def paid_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(UserBuy.waiting_for_receipt)
    await callback.message.answer("عکس رسید خودرا ارسال کنید:")

@dp.message(F.photo, UserBuy.waiting_for_receipt)
async def receive_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    char_id = data.get("buy_char_id")
    phone = data.get("phone", "نامشخص")
    receipt_id = message.photo[-1].file_id
    
    caption = (
        f"💰 درخواست خرید پت برای کاراکتر {char_id}\n\n"
        f"👤 کاربر: {message.from_user.full_name}\n"
        f"🆔 آیدی: <code>{message.from_user.id}</code>\n"
        f"🌐 یوزرنیم: @{message.from_user.username or 'ندارد'}\n"
        f"📱 شماره: {phone}\n\n"
        "آیا این واریزی تایید است؟"
    )
    
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data=f"approve_pet_{message.from_user.id}_{char_id}")
    b.button(text="❌ خیر", callback_data=f"reject_pet_{message.from_user.id}_{char_id}")
    
    await bot.send_photo(ADMIN_ID, photo=receipt_id, caption=caption, reply_markup=b.as_markup(), parse_mode="HTML")
    await message.reply("✅ رسید شما ارسال شد. پس از تایید، پت شما فعال خواهد شد.")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_pet_") | F.data.startswith("reject_pet_"))
async def admin_pet_approval(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    parts = callback.data.split("_")
    action = parts[0]
    user_id = parts[2]
    char_id = parts[3]
    
    if action == "approve":
        await set_setting(f"user_{user_id}_pet_{char_id}", "1") 
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تایید شد.")
        msg = 'پت شما فعال شد مبارک باشه رفیق <tg-emoji emoji-id="6041909294771739947">✨</tg-emoji>'
        await send_raw_api("sendMessage", {"chat_id": user_id, "text": parse_emojis(msg), "parse_mode": "HTML"})
    else:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
        await bot.send_message(user_id, "❌ متاسفانه رسید شما تایید نشد.")
        
    await callback.answer()

# ==========================================
# 🧩 ساختار کیبوردها (با استفاده از کدهای ایموجی پرمیوم کاربر)
# ==========================================
async def get_raw_main_keyboard(user_id: int):
    return [
        [{"text": "حساب کاربری", "callback_data": f"btn_profile_{user_id}", "icon_custom_emoji_id": await get_emoji("حساب کاربری", "5987865893084861885")},
         {"text": "بازار", "callback_data": f"btn_market_{user_id}", "icon_custom_emoji_id": await get_emoji("بازار", "5258024802010026053")}],
        [{"text": "داستانی", "callback_data": f"btn_story_{user_id}", "icon_custom_emoji_id": await get_emoji("داستانی", "5364052602357044385")},
         {"text": "مولتی(چند جهانی)", "callback_data": f"btn_multi_{user_id}", "icon_custom_emoji_id": await get_emoji("مولتی(چند جهانی)", "5361741454685256344")}],
        [{"text": "اسکین", "callback_data": f"btn_skin_{user_id}", "icon_custom_emoji_id": await get_emoji("اسکین", "5987973065403797894")},
         {"text": "ارتقا", "callback_data": f"btn_upgrade_{user_id}", "icon_custom_emoji_id": await get_emoji("ارتقا", "5375338737028841420")}],
        [{"text": "ماموریت ها", "callback_data": f"btn_missions_{user_id}", "icon_custom_emoji_id": await get_emoji("ماموریت ها", "5282996373229167849")}],
        [{"text": "جنگ ها", "callback_data": f"btn_wars_{user_id}", "icon_custom_emoji_id": await get_emoji("جنگ ها", "5453991094435997597")},
         {"text": "بازار سیاه", "callback_data": f"btn_blackmarket_{user_id}", "icon_custom_emoji_id": await get_emoji("بازار سیاه", "5296387887984580731")}],
        [{"text": "فروشگاه", "callback_data": f"btn_shop_{user_id}", "icon_custom_emoji_id": await get_emoji("فروشگاه", "5406683434124859552")},
         {"text": "لیدربرد", "callback_data": f"btn_leaderboard_{user_id}", "icon_custom_emoji_id": await get_emoji("لیدربرد", "5415655814079723871")}],
        [{"text": "کلن", "callback_data": f"btn_clan_{user_id}", "icon_custom_emoji_id": await get_emoji("کلن", "5978687277390371946")},
         {"text": "اخبار", "callback_data": f"btn_news_{user_id}", "icon_custom_emoji_id": await get_emoji("اخبار", "5443038326535759644")}],
        [{"text": "راهنما", "callback_data": f"btn_help_{user_id}", "icon_custom_emoji_id": await get_emoji("راهنما", "5282843764451195532")},
         {"text": "بستن منو", "callback_data": f"btn_close_{user_id}", "icon_custom_emoji_id": await get_emoji("بستن منو", "5210952531676504517")}]
    ]

async def get_raw_story_keyboard(user_id: int):
    return [
        [{"text": "ادامه بازی", "callback_data": f"btn_continue_{user_id}", "icon_custom_emoji_id": await get_emoji("ادامه بازی", "5206607081334906820")},
         {"text": "بازگشت", "callback_data": f"btn_backmain_{user_id}", "icon_custom_emoji_id": await get_emoji("بازگشت", "5210952531676504517")}]
    ]

async def get_raw_gamemenu_keyboard(user_id: int):
    return [
        [{"text": "شروع", "callback_data": f"btn_gamestart_{user_id}", "icon_custom_emoji_id": await get_emoji("شروع", "6021608144004716962")},
         {"text": "ادامه", "callback_data": f"btn_gamecontinue_{user_id}", "icon_custom_emoji_id": await get_emoji("ادامه", "6037142916160297263")}],
        [{"text": "ارتقا", "callback_data": f"btn_gameupg_{user_id}", "icon_custom_emoji_id": await get_emoji("ارتقا", "6043954888910576445")},
         {"text": "تسک", "callback_data": f"btn_gametask_{user_id}", "icon_custom_emoji_id": await get_emoji("تسک", "5780382873487939194")}],
        [{"text": "جوایز روزانه", "callback_data": f"btn_gamedaily_{user_id}", "icon_custom_emoji_id": await get_emoji("جوایز روزانه", "6034834521562553211")},
         {"text": "حیوانات نبرد", "callback_data": f"btn_gamepets_{user_id}", "icon_custom_emoji_id": await get_emoji("حیوانات نبرد", "6042051380879822629")}],
        [{"text": "راهنما", "callback_data": f"btn_guide_1_{user_id}", "icon_custom_emoji_id": await get_emoji("راهنمای داستانی", "6039577350868310365")},
         {"text": "بستن", "callback_data": f"btn_close_{user_id}", "icon_custom_emoji_id": await get_emoji("بستن", "6032606743500951856")}]
    ]

async def get_raw_upgrade_keyboard(user_id: int):
    return [
        [{"text": "چاقو", "callback_data": f"btn_showweapon_knife_{user_id}", "icon_custom_emoji_id": await get_emoji("چاقو", "5830442181906667908")}],
        [{"text": "شمشیر", "callback_data": f"btn_showweapon_sword_{user_id}", "icon_custom_emoji_id": await get_emoji("شمشیر", "5785098292312415025")}],
        [{"text": "کُلت", "callback_data": f"btn_showweapon_colt_{user_id}", "icon_custom_emoji_id": await get_emoji("کُلت", "6034845503793928402")}],
        [{"text": "کلاش", "callback_data": f"btn_showweapon_ak47_{user_id}", "icon_custom_emoji_id": await get_emoji("کلاش", "5181902025721381896")}],
        [{"text": "تعویض سلاح", "callback_data": f"btn_changeweapon_{user_id}", "icon_custom_emoji_id": await get_emoji("تعویض سلاح", "5361741454685256344")}],
        [{"text": "بازگشت", "callback_data": f"btn_backgamemenu_{user_id}", "icon_custom_emoji_id": await get_emoji("بازگشت", "5785177332595561481")}]
    ]

async def get_raw_character_keyboard(user_id: int):
    chars = []
    for i in range(1, 5):
        name = await get_setting(f"char{i}_name", f"کاراکتر {i}")
        emoji_id = await get_setting(f"char{i}_emoji")
        btn = {"text": name, "callback_data": f"btn_selectchar_{i}_{user_id}"}
        if emoji_id: btn["icon_custom_emoji_id"] = emoji_id
        chars.append(btn)
        
    return [
        [chars[0], chars[1]],
        [chars[2], chars[3]],
        [{"text": "بازگشت", "callback_data": f"btn_story_{user_id}", "icon_custom_emoji_id": "5210952531676504517"}]
    ]

# ==========================================
# 🚀 تریگر دقیق کلمه "تاتاروس"
# ==========================================
@dp.message(F.text == "تاتاروس")
async def trigger_tatarus_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        user_id = message.from_user.id
        photo = await get_setting("photo_main")
        kb = await get_raw_main_keyboard(user_id)
        
        payload = {
            "chat_id": message.chat.id, "parse_mode": "HTML",
            "reply_parameters": {"message_id": message.message_id},
            "reply_markup": {"inline_keyboard": kb}
        }
        
        if photo:
            payload["photo"] = photo
            payload["caption"] = MAIN_TEXT
            await send_raw_api("sendPhoto", payload)
        else:
            payload["text"] = MAIN_TEXT
            await send_raw_api("sendMessage", payload)

# ==========================================
# 🔄 جابجایی هوشمند بین منوها
# ==========================================
async def transition_menu(callback: types.CallbackQuery, photo_key: str, text: str, keyboard: list):
    target_photo = await get_setting(photo_key)
    has_media = True if (callback.message.photo or callback.message.animation or callback.message.video or callback.message.document) else False
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    
    reply_params = None
    if callback.message.reply_to_message:
        reply_params = {"message_id": callback.message.reply_to_message.message_id}
    
    if target_photo:
        if has_media:
            payload = {"chat_id": chat_id, "message_id": msg_id, "media": {"type": "photo", "media": target_photo, "caption": text, "parse_mode": "HTML"}, "reply_markup": {"inline_keyboard": keyboard}}
            await send_raw_api("editMessageMedia", payload)
        else:
            await callback.message.delete()
            payload = {"chat_id": chat_id, "photo": target_photo, "caption": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
            if reply_params: payload["reply_parameters"] = reply_params 
            await send_raw_api("sendPhoto", payload)
    else:
        if not has_media:
            payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
            await send_raw_api("editMessageText", payload)
        else:
            await callback.message.delete()
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
            if reply_params: payload["reply_parameters"] = reply_params 
            await send_raw_api("sendMessage", payload)

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای
# ==========================================
@dp.callback_query(F.data.startswith("btn_"))
async def handle_all_buttons(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    owner_id = int(parts[-1])
    
    if callback.from_user.id != owner_id:
        return await callback.answer("⛔️ این منو متعلق به شما نیست!", show_alert=True)

    if action == "close":
        await callback.message.delete()
    
    elif action == "story":
        kb = await get_raw_story_keyboard(owner_id)
        await transition_menu(callback, "photo_story", STORY_TEXT, kb)
        return await callback.answer()
        
    elif action == "backmain":
        kb = await get_raw_main_keyboard(owner_id)
        await transition_menu(callback, "photo_main", MAIN_TEXT, kb)
        return await callback.answer()
        
    elif action == "continue":
        kb = await get_raw_character_keyboard(owner_id)
        await transition_menu(callback, "photo_character", CHAR_SELECTION_TEXT, kb)
        return await callback.answer()
        
    elif action == "selectchar":
        char_id = parts[2]
        await set_setting(f"user_{owner_id}_char", char_id) 
        kb = await get_raw_gamemenu_keyboard(owner_id)
        await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
        return await callback.answer()

    elif action == "gamestart":
        return await callback.answer("⏳ در حال توسعه...", show_alert=True)

    elif action == "gameupg":
        kb = await get_raw_upgrade_keyboard(owner_id)
        await transition_menu(callback, "photo_upgrade", UPGRADE_TEXT, kb)
        return await callback.answer()

    elif action == "showweapon":
        weapon_type = parts[2]
        weapon_fa = [k for k, v in WEAPONS.items() if v == weapon_type][0]
        weapon_text = parse_emojis(f"بخش اختصاصی سلاح {weapon_fa} (در حال توسعه)")
        
        kb = [[{"text": "بازگشت", "callback_data": f"btn_backupgrade_{owner_id}", "icon_custom_emoji_id": await get_emoji("بازگشت", "5785177332595561481")}]]
        await transition_menu(callback, f"photo_weapon_{weapon_type}", weapon_text, kb)
        return await callback.answer()
        
    elif action == "backupgrade":
        kb = await get_raw_upgrade_keyboard(owner_id)
        await transition_menu(callback, "photo_upgrade", UPGRADE_TEXT, kb)
        return await callback.answer()

    elif action == "changeweapon":
        return await callback.answer("بخش تعویض سلاح به زودی اضافه می‌شود...", show_alert=True)

    elif action == "gamedaily":
        text = get_daily_reward_text()
        kb = [
            [{"text": "دریافت جوایز روزانه", "callback_data": f"btn_claimdaily_{owner_id}", "icon_custom_emoji_id": await get_emoji("دریافت جوایز روزانه", "6028565819225542441")}],
            [{"text": "بازگشت", "callback_data": f"btn_backgamemenu_{owner_id}", "icon_custom_emoji_id": await get_emoji("بازگشت", "6032606743500951856")}]
        ]
        await transition_menu(callback, "photo_gamedaily", text, kb)
        return await callback.answer()

    elif action == "claimdaily":
        kb = await get_raw_gamemenu_keyboard(owner_id)
        await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
        return await callback.answer("🎉 جوایز روزانه با موفقیت به حساب شما اضافه شد!", show_alert=True)

    elif action == "gamepets":
        char_id = await get_setting(f"user_{owner_id}_char", "1")
        is_purchased = await get_setting(f"user_{owner_id}_pet_{char_id}") == "1"
        
        pet_text_raw = await get_setting("pet_text", "متن حیوان هنوز تنظیم نشده است.")
        pet_text = parse_emojis(pet_text_raw)
        
        if is_purchased: pet_text += "\n\nخریداری شده <tg-emoji emoji-id='6028565819225542441'>✅</tg-emoji>"
        else: pet_text += "\n\nخریداری نشده <tg-emoji emoji-id='6032606743500951856'>❌</tg-emoji>"

        kb = []
        if is_purchased: kb.append([{"text": "فعال کردن برای نبرد", "callback_data": f"btn_activatepet_{char_id}_{owner_id}", "icon_custom_emoji_id": "5780857858216173092"}])
        else: kb.append([{"text": "خریدن حیوان", "url": f"https://t.me/{BOT_USERNAME}?start=buypet_{char_id}", "icon_custom_emoji_id": "6028565819225542441"}])
            
        kb.append([{"text": "بازگشت", "callback_data": f"btn_backgamemenu_{owner_id}", "icon_custom_emoji_id": "6032606743500951856"}])
        
        await transition_menu(callback, f"photo_pet_{char_id}", pet_text, kb)
        return await callback.answer()

    elif action == "activatepet":
        return await callback.answer("⚔️ پت شما با موفقیت برای نبرد فعال شد!", show_alert=True)

    elif action == "guide":
        page = int(parts[2])
        total_pages = int(await get_setting("guide_pages_count", "1"))
        text_raw = await get_setting(f"guide_text_{page}", "متن راهنما تنظیم نشده است.")
        text_parsed = parse_emojis(text_raw)
        
        nav_btns = []
        if page > 1: nav_btns.append({"text": "قبلی", "callback_data": f"btn_guide_{page-1}_{owner_id}"})
        if page < total_pages: nav_btns.append({"text": "بعدی", "callback_data": f"btn_guide_{page+1}_{owner_id}"})
        
        kb = []
        if nav_btns: kb.append(nav_btns)
        kb.append([{"text": "بازگشت", "callback_data": f"btn_backgamemenu_{owner_id}"}])
        
        await transition_menu(callback, f"photo_guide_{page}", text_parsed, kb)
        return await callback.answer()

    elif action == "backgamemenu":
        kb = await get_raw_gamemenu_keyboard(owner_id)
        await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
        return await callback.answer()

    else:
        await callback.answer("⏳ در حال توسعه...", show_alert=True)

# ==========================================
# 🔥 اجرا
# ==========================================
async def main():
    global BOT_USERNAME
    await init_db()
    me = await bot.get_me()
    BOT_USERNAME = me.username
    print(f"🤖 ربات تاتاروس ({BOT_USERNAME}) با موفقیت به نسخه پایدار برگردانده شد!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
