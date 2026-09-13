import asyncio
import logging
import os
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
# 🗄 دیتابیس (ذخیره عکس‌های ادمین)
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

async def get_photo(menu_type: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (f"photo_{menu_type}",)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None  # اگر عکسی تنظیم نشده باشد، مقدار None برمی‌گرداند

async def set_photo(menu_type: str, file_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (f"photo_{menu_type}", file_id))
        await db.commit()

# ==========================================
# 🧩 ساختار دکمه‌ها قفل شده روی آیدی کاربر 
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

@dp.message(F.text == "تغییر عکس منو تاتاروس")
async def cmd_change_main_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.set_state(AdminSetup.waiting_for_main_photo)
    await message.reply("📸 لطفاً عکس جدید برای **منوی اصلی** را ارسال کنید:")

@dp.message(F.text == "تغییر عکس اوپن داستانی")
async def cmd_change_story_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.set_state(AdminSetup.waiting_for_story_photo)
    await message.reply("📸 لطفاً عکس جدید برای **بخش داستانی** را ارسال کنید:")

@dp.message(F.photo, AdminSetup.waiting_for_main_photo)
@dp.message(F.photo, AdminSetup.waiting_for_story_photo)
async def receive_admin_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    current_state = await state.get_state()
    menu_type = "main" if current_state == AdminSetup.waiting_for_main_photo.state else "story"
    
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
        await set_photo(data['target_menu'], data['temp_file_id'])
        await callback.message.edit_caption(caption="✅ عکس ذخیره شد!")
    else:
        await callback.message.edit_caption(caption="❌ عملیات رد شد.")
    await state.clear()
    await callback.answer()

# ==========================================
# 🚀 هندلر گروه (فراخوانی تاتاروس)
# ==========================================
@dp.message(F.text.contains("تاتاروس") & ~F.text.contains("تغییر عکس"))
async def trigger_tatarus_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        user_id = message.from_user.id
        photo = await get_photo("main")
        
        payload = {
            "chat_id": message.chat.id,
            "parse_mode": "HTML",
            "reply_parameters": {"message_id": message.message_id},
            "reply_markup": {
                "inline_keyboard": get_raw_main_keyboard(user_id)
            }
        }
        
        # اگر عکس تنظیم شده بود sendPhoto در غیر این صورت sendMessage
        if photo:
            payload["photo"] = photo
            payload["caption"] = MAIN_TEXT
            await send_raw_api("sendPhoto", payload)
        else:
            payload["text"] = MAIN_TEXT
            await send_raw_api("sendMessage", payload)

# ==========================================
# 🔄 تابع جادویی مدیریت جابجایی بین منوها (با/بدون عکس)
# ==========================================
async def transition_menu(callback: types.CallbackQuery, target_menu: str, text: str, keyboard: list):
    target_photo = await get_photo(target_menu)
    has_media = bool(callback.message.photo) # آیا پیام فعلی عکس دارد؟
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    
    if target_photo:
        # اگر منوی مقصد عکس دارد
        if has_media:
            # هر دو عکس دارند -> فقط ویرایش مدیا
            payload = {
                "chat_id": chat_id, "message_id": msg_id,
                "media": {"type": "photo", "media": target_photo, "caption": text, "parse_mode": "HTML"},
                "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("editMessageMedia", payload)
        else:
            # فعلی متنی است، مقصد عکس‌دار -> پیام قبلی باید پاک و جدید ارسال شود
            await callback.message.delete()
            payload = {
                "chat_id": chat_id, "photo": target_photo, "caption": text,
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("sendPhoto", payload)
    else:
        # اگر منوی مقصد عکس ندارد
        if not has_media:
            # هر دو متنی هستند -> فقط ویرایش متن
            payload = {
                "chat_id": chat_id, "message_id": msg_id, "text": text,
                "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}
            }
            await send_raw_api("editMessageText", payload)
        else:
            # فعلی عکس‌دار است، مقصد متنی -> پیام قبلی باید پاک و جدید ارسال شود
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
    owner_id = int(parts[2])
    
    if callback.fromuser.id != owner_id:
        return await callback.answer("⛔️ این منو متعلق به شما نیست!", show_alert=True)

    if action == "close":
        await callback.message.delete()
        return await callback.answer("منو بسته شد.", show_alert=False)
        
    elif action == "story":
        await transition_menu(callback, "story", STORY_TEXT, get_raw_story_keyboard(owner_id))
        return await callback.answer()

    elif action == "backmain":
        await transition_menu(callback, "main", MAIN_TEXT, get_raw_main_keyboard(owner_id))
        return await callback.answer()

    else:
        await callback.answer("⏳ در حال توسعه...", show_alert=True)

# ==========================================
# 🔥 اجرای هسته
# ==========================================
async def main():
    await init_db()
    print("🤖 ربات تاتاروس (بدون عکس پیش‌فرض) با موفقیت روشن شد!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
