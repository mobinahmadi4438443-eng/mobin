import asyncio
import logging
import os
import re
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ تنظیمات اولیه
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_را_اینجا_بگذار")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789)) # آیدی عددی مالک ربات
DB_NAME = "tatarus.db"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 🗄 دیتابیس (ذخیره تنظیمات، عکس‌ها و کاراکترها)
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await db.commit()

async def get_setting(key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

# ==========================================
# 🧩 ساختار دکمه‌ها قفل شده (منوی اصلی و داستانی)
# ==========================================
def get_raw_main_keyboard(user_id: int):
    return [
        [
            {"text": "حساب کاربری", "callback_data": f"btn_profile_{user_id}", "icon_custom_emoji_id": "5987865893084861885"},
            {"text": "بازار", "callback_data": f"btn_market_{user_id}", "icon_custom_emoji_id": "5258024802010026053"}
        ],
        [
            {"text": "داستانی", "callback_data": f"btn_story_{user_id}", "icon_custom_emoji_id": "5364052602357044385"},
            {"text": "مولتی(چند جهانی)", "callback_data": f"btn_multi_{user_id}", "icon_custom_emoji_id": "5361741454685256344"}
        ],
        [
            {"text": "اسکین", "callback_data": f"btn_skin_{user_id}", "icon_custom_emoji_id": "5987973065403797894"},
            {"text": "ارتقا", "callback_data": f"btn_upgrade_{user_id}", "icon_custom_emoji_id": "5375338737028841420"}
        ],
        [
            {"text": "ماموریت ها", "callback_data": f"btn_missions_{user_id}", "icon_custom_emoji_id": "5282996373229167849"}
        ],
        [
            {"text": "جنگ ها", "callback_data": f"btn_wars_{user_id}", "icon_custom_emoji_id": "5453991094435997597"},
            {"text": "بازار سیاه", "callback_data": f"btn_blackmarket_{user_id}", "icon_custom_emoji_id": "5296387887984580731"}
        ],
        [
            {"text": "فروشگاه", "callback_data": f"btn_shop_{user_id}", "icon_custom_emoji_id": "5406683434124859552"},
            {"text": "لیدربرد", "callback_data": f"btn_leaderboard_{user_id}", "icon_custom_emoji_id": "5415655814079723871"}
        ],
        [
            {"text": "کلن", "callback_data": f"btn_clan_{user_id}", "icon_custom_emoji_id": "5978687277390371946"},
            {"text": "اخبار", "callback_data": f"btn_news_{user_id}", "icon_custom_emoji_id": "5443038326535759644"}
        ],
        [
            {"text": "راهنما", "callback_data": f"btn_help_{user_id}", "icon_custom_emoji_id": "5282843764451195532"},
            {"text": "بستن منو", "callback_data": f"btn_close_{user_id}", "icon_custom_emoji_id": "5210952531676504517"}
        ]
    ]

def get_raw_story_keyboard(user_id: int):
    return [
        [
            {"text": "ادامه بازی", "callback_data": f"btn_continue_{user_id}", "icon_custom_emoji_id": "5206607081334906820"},
            {"text": "بازگشت", "callback_data": f"btn_backmain_{user_id}", "icon_custom_emoji_id": "5210952531676504517"}
        ]
    ]

# کیبورد کاراکترها (خواندن نام و ایموجی از دیتابیس)
async def get_raw_character_keyboard(user_id: int):
    chars = []
    for i in range(1, 5):
        name = await get_setting(f"char{i}_name") or f"کاراکتر {i}"
        emoji_id = await get_setting(f"char{i}_emoji")
        
        btn = {"text": name, "callback_data": f"btn_selectchar_{i}_{user_id}"}
        if emoji_id:
            btn["icon_custom_emoji_id"] = emoji_id
        chars.append(btn)
        
    return [
        [chars[0], chars[1]], # ردیف اول: کاراکتر ۱ و ۲
        [chars[2], chars[3]], # ردیف دوم: کاراکتر ۳ و ۴
        [{"text": "بازگشت", "callback_data": f"btn_story_{user_id}", "icon_custom_emoji_id": "5210952531676504517"}] # بازگشت به داستانی
    ]

# ==========================================
# 📝 متن‌های ربات 
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

CHAR_SELECTION_TEXT = 'کاراکتر مورد نظر خودرا انتخاب کنید <tg-emoji emoji-id="5019617635629794161">👇</tg-emoji>'

# ==========================================
# 📡 متدهای خام ارتباطی با تلگرام
# ==========================================
async def send_raw_api(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"):
                logging.error(f"Telegram API Error: {result}")

# ==========================================
# 🖼 مدیریت آپلود عکس توسط ادمین (FSM)
# ==========================================
class AdminSetup(StatesGroup):
    waiting_for_main_photo = State()
    waiting_for_story_photo = State()
    waiting_for_character_photo = State()
    waiting_for_char_names = State()

@dp.message(F.text.in_({"تغییر عکس منو تاتاروس", "تغییر عکس اوپن داستانی", "تغییر عکس کاراکتر"}))
async def cmd_change_photos(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    
    if message.text == "تغییر عکس منو تاتاروس":
        await state.set_state(AdminSetup.waiting_for_main_photo)
        await message.reply("📸 عکس جدید برای **منوی اصلی** را ارسال کنید:")
    elif message.text == "تغییر عکس اوپن داستانی":
        await state.set_state(AdminSetup.waiting_for_story_photo)
        await message.reply("📸 عکس جدید برای **بخش داستانی** را ارسال کنید:")
    elif message.text == "تغییر عکس کاراکتر":
        await state.set_state(AdminSetup.waiting_for_character_photo)
        await message.reply("📸 عکس جدید برای **بخش انتخاب کاراکتر** را ارسال کنید:")

@dp.message(F.photo, AdminSetup.waiting_for_main_photo)
@dp.message(F.photo, AdminSetup.waiting_for_story_photo)
@dp.message(F.photo, AdminSetup.waiting_for_character_photo)
async def receive_admin_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    current_state = await state.get_state()
    
    if current_state == AdminSetup.waiting_for_main_photo.state: menu_type = "main"
    elif current_state == AdminSetup.waiting_for_story_photo.state: menu_type = "story"
    else: menu_type = "character"
    
    await state.update_data(temp_file_id=file_id, target_menu=menu_type)
    
    b = InlineKeyboardBuilder()
    b.button(text="✅ تایید کردن", callback_data="admin_confirm_photo")
    b.button(text="❌ رد کردن", callback_data="admin_reject_photo")
    await message.reply_photo(photo=file_id, caption="آیا این عکس تایید است؟", reply_markup=b.as_markup())

@dp.callback_query(F.data.in_({"admin_confirm_photo", "admin_reject_photo"}))
async def process_admin_photo_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    if callback.data == "admin_confirm_photo":
        await set_setting(f"photo_{data['target_menu']}", data['temp_file_id'])
        await callback.message.edit_caption(caption="✅ عکس با موفقیت ذخیره شد!")
    else:
        await callback.message.edit_caption(caption="❌ عملیات رد شد.")
    await state.clear()
    await callback.answer()

# ==========================================
# 📝 مدیریت تنظیم اسامی کاراکترها (Loop FSM)
# ==========================================
@dp.message(F.text == "تغییر اسم کاراکتر ها")
async def cmd_change_char_names(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.set_state(AdminSetup.waiting_for_char_names)
    await state.update_data(current_char=1) # شروع از کاراکتر اول
    await message.reply("تغییر اسم کاراکتر ها:\nاسم اولین کاراکتر را انتخاب کنید (میتوانید کد ایموجی را هم کنارش بنویسید):")

@dp.message(AdminSetup.waiting_for_char_names)
async def receive_char_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_char = data.get("current_char", 1)
    
    # هوش مصنوعی جداکننده متن از آیدی ایموجی (اعداد بالای 15 رقم)
    raw_text = message.text
    match = re.search(r'\b(\d{15,22})\b', raw_text)
    
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
    
    confirm_text = f"آیا این اسم تایید است؟\n\nنام: `{name}`"
    if emoji_id: confirm_text += f"\nکد ایموجی استخراج شده: `{emoji_id}`"
    
    await message.reply(confirm_text, reply_markup=b.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.in_({"char_confirm_yes", "char_confirm_no"}))
async def process_char_name_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    current_char = data.get("current_char", 1)
    
    if callback.data == "char_confirm_yes":
        await set_setting(f"char{current_char}_name", data["temp_name"])
        if data["temp_emoji"]:
            await set_setting(f"char{current_char}_emoji", data["temp_emoji"])
        else:
            await set_setting(f"char{current_char}_emoji", "") # پاک کردن ایموجی قبلی در صورت نداشتن
        await callback.message.edit_text(f"✅ اسم کاراکتر {current_char} با موفقیت ذخیره شد.")
    else:
        await callback.message.edit_text(f"❌ اسمی برای کاراکتر {current_char} ذخیره نشد.")
        
    next_char = current_char + 1
    if next_char > 4:
        await callback.message.answer("🎉 تنظیمات اسم هر ۴ کاراکتر به پایان رسید.")
        await state.clear()
    else:
        await state.update_data(current_char=next_char)
        await callback.message.answer(f"حالا اسم کاراکتر {next_char} را انتخاب کنید:")

# ==========================================
# 🚀 هندلر گروه (فراخوانی تاتاروس)
# ==========================================
@dp.message(F.text.contains("تاتاروس") & ~F.text.contains("تغییر عکس"))
async def trigger_tatarus_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        user_id = message.from_user.id
        photo = await get_setting("photo_main")
        
        payload = {
            "chat_id": message.chat.id,
            "parse_mode": "HTML",
            "reply_parameters": {"message_id": message.message_id},
            "reply_markup": {
                "inline_keyboard": get_raw_main_keyboard(user_id)
            }
        }
        
        if photo:
            payload["photo"] = photo
            payload["caption"] = MAIN_TEXT
            await send_raw_api("sendPhoto", payload)
        else:
            payload["text"] = MAIN_TEXT
            await send_raw_api("sendMessage", payload)

# ==========================================
# 🔄 تابع جادویی مدیریت جابجایی بین منوها
# ==========================================
async def transition_menu(callback: types.CallbackQuery, target_menu: str, text: str, keyboard: list):
    target_photo = await get_setting(f"photo_{target_menu}")
    has_media = bool(callback.message.photo)
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    
    if target_photo:
        if has_media:
            payload = {
                "chat_id": chat_id, "message_id": msg_id,
                "media": {"type": "photo", "media": target_photo, "caption": text, "parse_mode": "HTML"},
                "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("editMessageMedia", payload)
        else:
            await callback.message.delete()
            payload = {
                "chat_id": chat_id, "photo": target_photo, "caption": text,
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("sendPhoto", payload)
    else:
        if not has_media:
            payload = {
                "chat_id": chat_id, "message_id": msg_id, "text": text,
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("editMessageText", payload)
        else:
            await callback.message.delete()
            payload = {
                "chat_id": chat_id, "text": text,
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("sendMessage", payload)

# ==========================================
# 🎛 هندلرهای دکمه‌های شیشه‌ای (Anti-Hijack)
# ==========================================
@dp.callback_query(F.data.startswith("btn_"))
async def handle_all_buttons(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    owner_id = int(parts[-1]) # آیدی همیشه قسمت آخر callback_data است
    
    if callback.from_user.id != owner_id:
        return await callback.answer("⛔️ این منو متعلق به شما نیست!", show_alert=True)

    if action == "close":
        await callback.message.delete()
        return await callback.answer("منو بسته شد.", show_alert=False)
        
    elif action == "story":
        await transition_menu(callback, "story", STORY_TEXT, get_raw_story_keyboard(owner_id))
        return await callback.answer()

    elif action == "continue":
        # دریافت کیبورد کاراکترها به صورت زنده از دیتابیس
        char_keyboard = await get_raw_character_keyboard(owner_id)
        await transition_menu(callback, "character", CHAR_SELECTION_TEXT, char_keyboard)
        return await callback.answer()

    elif action == "backmain":
        await transition_menu(callback, "main", MAIN_TEXT, get_raw_main_keyboard(owner_id))
        return await callback.answer()
        
    elif action == "selectchar":
        char_number = parts[2]
        return await callback.answer(f"🎉 شما کاراکتر {char_number} را انتخاب کردید! (در حال توسعه)", show_alert=True)

    else:
        await callback.answer("⏳ در حال توسعه...", show_alert=True)

# ==========================================
# 🔥 اجرای هسته
# ==========================================
async def main():
    await init_db()
    print("🤖 ربات تاتاروس با سیستم انتخاب کاراکتر هوشمند روشن شد!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
