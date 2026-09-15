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
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))
DB_NAME = "tatarus.db"

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
# 🧩 دریافت ایموجی‌های داینامیک
# ==========================================
async def get_emoji(btn_name: str, default_id: str):
    return await get_setting(f"emoji_{btn_name}", default_id)

# ==========================================
# 🧩 ساختار دکمه‌ها (Async)
# ==========================================
async def get_raw_main_keyboard(user_id: int):
    return [
        [
            {"text": "حساب کاربری", "callback_data": f"btn_profile_{user_id}", "icon_custom_emoji_id": await get_emoji("حساب کاربری", "5987865893084861885")},
            {"text": "بازار", "callback_data": f"btn_market_{user_id}", "icon_custom_emoji_id": await get_emoji("بازار", "5258024802010026053")}
        ],
        [
            {"text": "داستانی", "callback_data": f"btn_story_{user_id}", "icon_custom_emoji_id": await get_emoji("داستانی", "5364052602357044385")},
            {"text": "مولتی(چند جهانی)", "callback_data": f"btn_multi_{user_id}", "icon_custom_emoji_id": await get_emoji("مولتی(چند جهانی)", "5361741454685256344")}
        ],
        [
            {"text": "اسکین", "callback_data": f"btn_skin_{user_id}", "icon_custom_emoji_id": await get_emoji("اسکین", "5987973065403797894")},
            {"text": "ارتقا", "callback_data": f"btn_upgrade_{user_id}", "icon_custom_emoji_id": await get_emoji("ارتقا", "5375338737028841420")}
        ],
        [
            {"text": "ماموریت ها", "callback_data": f"btn_missions_{user_id}", "icon_custom_emoji_id": await get_emoji("ماموریت ها", "5282996373229167849")}
        ],
        [
            {"text": "جنگ ها", "callback_data": f"btn_wars_{user_id}", "icon_custom_emoji_id": await get_emoji("جنگ ها", "5453991094435997597")},
            {"text": "بازار سیاه", "callback_data": f"btn_blackmarket_{user_id}", "icon_custom_emoji_id": await get_emoji("بازار سیاه", "5296387887984580731")}
        ],
        [
            {"text": "فروشگاه", "callback_data": f"btn_shop_{user_id}", "icon_custom_emoji_id": await get_emoji("فروشگاه", "5406683434124859552")},
            {"text": "لیدربرد", "callback_data": f"btn_leaderboard_{user_id}", "icon_custom_emoji_id": await get_emoji("لیدربرد", "5415655814079723871")}
        ],
        [
            {"text": "کلن", "callback_data": f"btn_clan_{user_id}", "icon_custom_emoji_id": await get_emoji("کلن", "5978687277390371946")},
            {"text": "اخبار", "callback_data": f"btn_news_{user_id}", "icon_custom_emoji_id": await get_emoji("اخبار", "5443038326535759644")}
        ],
        [
            {"text": "راهنما", "callback_data": f"btn_help_{user_id}", "icon_custom_emoji_id": await get_emoji("راهنما", "5282843764451195532")},
            {"text": "بستن منو", "callback_data": f"btn_close_{user_id}", "icon_custom_emoji_id": await get_emoji("بستن منو", "5210952531676504517")}
        ]
    ]

async def get_raw_story_keyboard(user_id: int):
    return [
        [
            {"text": "ادامه بازی", "callback_data": f"btn_continue_{user_id}", "icon_custom_emoji_id": await get_emoji("ادامه بازی", "5206607081334906820")},
            {"text": "بازگشت", "callback_data": f"btn_backmain_{user_id}", "icon_custom_emoji_id": await get_emoji("بازگشت", "5210952531676504517")}
        ]
    ]

async def get_raw_gamemenu_keyboard(user_id: int):
    return [
        [
            {"text": "شروع", "callback_data": f"btn_gamestart_{user_id}", "icon_custom_emoji_id": await get_emoji("شروع", "6021608144004716962")},
            {"text": "ادامه", "callback_data": f"btn_gamecontinue_{user_id}", "icon_custom_emoji_id": await get_emoji("ادامه", "6037142916160297263")}
        ],
        [
            {"text": "ارتقا", "callback_data": f"btn_gameupg_{user_id}", "icon_custom_emoji_id": await get_emoji("ارتقا", "6043954888910576445")},
            {"text": "تسک", "callback_data": f"btn_gametask_{user_id}", "icon_custom_emoji_id": await get_emoji("تسک", "5780382873487939194")}
        ],
        [
            {"text": "جوایز روزانه", "callback_data": f"btn_gamedaily_{user_id}", "icon_custom_emoji_id": await get_emoji("جوایز روزانه", "6034834521562553211")},
            {"text": "حیوانات نبرد", "callback_data": f"btn_gamepets_{user_id}", "icon_custom_emoji_id": await get_emoji("حیوانات نبرد", "6042051380879822629")}
        ],
        [
            {"text": "راهنما", "callback_data": f"btn_guide_1_{user_id}", "icon_custom_emoji_id": await get_emoji("راهنمای داستانی", "6039577350868310365")},
            {"text": "بستن", "callback_data": f"btn_close_{user_id}", "icon_custom_emoji_id": await get_emoji("بستن", "6032606743500951856")}
        ]
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
# 📝 متن‌ها و پردازشگر هوشمند ایموجی
# ==========================================
def parse_emojis(text: str) -> str:
    return re.sub(r'(\d{15,22})', r'<tg-emoji emoji-id="\1">✨</tg-emoji>', text)

MAIN_TEXT = parse_emojis("5282974228377789040 <b>منوی اصلی بازی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
GAME_MENU_TEXT = parse_emojis("5282974228377789040 <b>منوی داستانی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
CHAR_SELECTION_TEXT = parse_emojis("کاراکتر مورد نظر خودرا انتخاب کنید 5019617635629794161")

# متن اوپنینگ داستانی (اصلاح شده و کامل)
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

# ==========================================
# 📡 ارتباط خام
# ==========================================
async def send_raw_api(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"): logging.error(f"Telegram API Error: {result}")

# ==========================================
# 🖼 ماشین وضعیت FSM ادمین
# ==========================================
class AdminSetup(StatesGroup):
    waiting_for_photo = State()
    waiting_for_emoji = State()
    guide_text_page = State()
    guide_photo_page = State()

# 1. تغییر عکس‌ها
@dp.message(F.text.in_({"تغییر عکس منو تاتاروس", "تغییر عکس اوپن داستانی", "تغییر عکس کاراکتر", "تغییر عکس منو داستانی"}))
async def cmd_change_photos(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    
    target = "main"
    if "اوپن داستانی" in message.text: target = "story"
    elif "کاراکتر" in message.text: target = "character"
    elif "منو داستانی" in message.text: target = "gamemenu"
    
    await state.set_state(AdminSetup.waiting_for_photo)
    await state.update_data(target_menu=target)
    await message.reply("📸 عکس مورد نظر را ارسال کنید:")

@dp.message(F.photo, AdminSetup.waiting_for_photo)
async def receive_photo(message: types.Message, state: FSMContext):
    await state.update_data(temp_file_id=message.photo[-1].file_id)
    b = InlineKeyboardBuilder()
    b.button(text="✅ بله", callback_data="admin_confirm_photo")
    b.button(text="❌ خیر", callback_data="admin_reject")
    await message.reply("آیا عکس تایید است؟", reply_markup=b.as_markup())

# 2. تغییر ایموجی دکمه‌ها
@dp.message(F.text.startswith("تغییر ایموجی دکمه "))
async def cmd_change_emoji(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    btn_name = message.text.replace("تغییر ایموجی دکمه ", "").split("/")[0].strip()
    
    await state.set_state(AdminSetup.waiting_for_emoji)
    await state.update_data(target_btn=btn_name)
    await message.reply(f"کد ایموجی جدید برای دکمه «{btn_name}» را ارسال کنید:")

@dp.message(AdminSetup.waiting_for_emoji)
async def receive_emoji_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    emoji_code = message.text.strip()
    await set_setting(f"emoji_{data['target_btn']}", emoji_code)
    await message.reply(f"✅ ایموجی دکمه {data['target_btn']} به {emoji_code} تغییر یافت.")
    await state.clear()

# 3. سیستم چند صفحه‌ای راهنما (متن)
@dp.message(F.text == "تغییر راهنمای داستانی")
async def cmd_change_guide_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    current_text = await get_setting("guide_text_1", "تنظیم نشده")
    await state.set_state(AdminSetup.guide_text_page)
    await state.update_data(current_page=1)
    await message.reply(f"متن فعلی راهنمای داستانی صفحه اول:\n\n{current_text}\n\nمتن جدید را ارسال کنید:")

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
    b.button(text="❌ خیر", callback_data="admin_reject")
    await callback.message.edit_text("صفحه بعد رو میخواهید اضافه کنید یا نه؟", reply_markup=b.as_markup())

@dp.callback_query(F.data == "guide_next_page_yes")
async def next_page_guide_text(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    next_page = data.get("current_page", 1) + 1
    await state.update_data(current_page=next_page)
    await callback.message.edit_text(f"متن جدید برای صفحه {next_page} را ارسال کنید:")

# 4. سیستم چند صفحه‌ای راهنما (عکس)
@dp.message(F.text == "تغییر عکس راهنمای داستانی")
async def cmd_change_guide_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.set_state(AdminSetup.guide_photo_page)
    await state.update_data(current_page=1)
    await message.reply("📸 عکس راهنمای داستانی (صفحه 1) را ارسال کنید:")

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
        await callback.message.edit_text("✅ عکس تمامی صفحات راهنما ذخیره شد.")
        await state.clear()

# رد کردن عمومی
@dp.callback_query(F.data == "admin_reject")
async def reject_admin(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("❌ عملیات لغو شد.")
    await state.clear()

@dp.callback_query(F.data == "admin_confirm_photo")
async def confirm_photo(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    await set_setting(f"photo_{data['target_menu']}", data['temp_file_id'])
    await callback.message.edit_text("✅ عکس با موفقیت ذخیره شد!")
    await state.clear()

# ==========================================
# 🚀 تریگر دقیق کلمه "تاتاروس" (فقط به صورت خالی)
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
# 🔄 جابجایی بین منوها
# ==========================================
async def transition_menu(callback: types.CallbackQuery, photo_key: str, text: str, keyboard: list):
    target_photo = await get_setting(photo_key)
    has_media = bool(callback.message.photo)
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    
    if target_photo:
        if has_media:
            payload = {"chat_id": chat_id, "message_id": msg_id, "media": {"type": "photo", "media": target_photo, "caption": text, "parse_mode": "HTML"}, "reply_markup": {"inline_keyboard": keyboard}}
            await send_raw_api("editMessageMedia", payload)
        else:
            await callback.message.delete()
            payload = {"chat_id": chat_id, "photo": target_photo, "caption": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
            await send_raw_api("sendPhoto", payload)
    else:
        if not has_media:
            payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
            await send_raw_api("editMessageText", payload)
        else:
            await callback.message.delete()
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}}
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
        # فراخوانی متن داستان با ایموجی‌های کامل
        await transition_menu(callback, "photo_story", STORY_TEXT, kb)
        return await callback.answer()
        
    elif action == "backmain":
        kb = await get_raw_main_keyboard(owner_id)
        # دکمه بازگشت در منوی داستانی پیام را به منوی اصلی برمی‌گرداند
        await transition_menu(callback, "photo_main", MAIN_TEXT, kb)
        return await callback.answer()
        
    elif action == "continue":
        kb = await get_raw_character_keyboard(owner_id)
        await transition_menu(callback, "photo_character", CHAR_SELECTION_TEXT, kb)
        return await callback.answer()
        
    elif action == "selectchar":
        kb = await get_raw_gamemenu_keyboard(owner_id)
        await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
        return await callback.answer()
        
    elif action == "guide":
        page = int(parts[2])
        total_pages = int(await get_setting("guide_pages_count", "1"))
        text_raw = await get_setting(f"guide_text_{page}", "متن راهنما تنظیم نشده است.")
        text_parsed = parse_emojis(text_raw)
        
        # ساخت کیبورد راهنما
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
    await init_db()
    print("🤖 ربات تاتاروس: متن اوپنینگ و بازگشت داستانی فیکس شد!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
