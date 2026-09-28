import os
import asyncio
import re
import aiohttp
import json
import time
from datetime import datetime
from pyrogram import Client
import aiosqlite

# =================================================================
# متغیرهای محیطی
# =================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()

try:
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
except ValueError:
    OWNER_ID = 0 

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
GROUP_ID = -1004426176128
CHECKER_BOT_USERNAME = "HashTrxCheckerBot"
DB_NAME = "bot_database.db"

# =================================================================
# دیتابیس SQLite
# =================================================================
async def init_db():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    auto_delete INTEGER DEFAULT 0,
                    stars_profit REAL DEFAULT 20.0,
                    premium_profit REAL DEFAULT 20.0,
                    checker_api_id INTEGER NULL,
                    checker_api_hash TEXT NULL,
                    checker_session TEXT NULL,
                    banners TEXT
                )
            """)
            await db.commit()
        print("✅ دیتابیس با موفقیت متصل شد.")
        return True
    except Exception as e:
        print(f"❌ خطا در ساخت دیتابیس: {e}")
        return False

async def get_user_data(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute("INSERT INTO users (user_id, banners) VALUES (?, '{}')", (user_id,))
                await db.commit()
                return {"_id": user_id, "banners": {}, "auto_delete": False, "stars_profit": 20.0, "premium_profit": 20.0, "checker": {}}
            
            banners = json.loads(row['banners']) if row['banners'] else {}
            user = {
                "_id": user_id,
                "auto_delete": bool(row['auto_delete']),
                "stars_profit": float(row['stars_profit']),
                "premium_profit": float(row['premium_profit']),
                "banners": banners,
                "checker": {}
            }
            if row['checker_session']:
                user['checker'] = {"api_id": row['checker_api_id'], "api_hash": row['checker_api_hash'], "session_string": row['checker_session']}
            return user

async def update_user_data(user_id, update_dict):
    sets, values = [], []
    if "banners" in update_dict:
        sets.append("banners = ?"); values.append(json.dumps(update_dict["banners"]))
    if "stars_profit" in update_dict:
        sets.append("stars_profit = ?"); values.append(update_dict["stars_profit"])
    if "premium_profit" in update_dict:
        sets.append("premium_profit = ?"); values.append(update_dict["premium_profit"])
    if "auto_delete" in update_dict:
        sets.append("auto_delete = ?"); values.append(int(update_dict["auto_delete"]))
    if "checker" in update_dict:
        checker = update_dict["checker"]
        sets.append("checker_api_id = ?"); values.append(checker.get("api_id"))
        sets.append("checker_api_hash = ?"); values.append(checker.get("api_hash"))
        sets.append("checker_session = ?"); values.append(checker.get("session_string"))
        
    if not sets: return
    query = f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?"
    values.append(user_id)
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(query, tuple(values))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            users = []
            for row in rows:
                banners = json.loads(row['banners']) if row['banners'] else {}
                u = {
                    "_id": row['user_id'],
                    "auto_delete": bool(row['auto_delete']),
                    "stars_profit": float(row['stars_profit']),
                    "premium_profit": float(row['premium_profit']),
                    "banners": banners,
                    "checker": {}
                }
                if row['checker_session']:
                    u['checker'] = {"api_id": row['checker_api_id'], "api_hash": row['checker_api_hash'], "session_string": row['checker_session']}
                users.append(u)
            return users

# =================================================================
# توابع پایه و هندل کردن هوشمند ایموجی‌ها
# =================================================================
user_states = {}
temp_login_clients = {} 

async def api_request(session, method, payload=None):
    url = BASE_URL + method
    try:
        async with session.post(url, json=payload) as response:
            return await response.json()
    except Exception as e:
        print(f"❌ خطای شبکه: {e}")
        return {}

def convert_persian_to_english_digits(text):
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

def format_custom_emojis(text):
    """
    هر جا در متن (اول، وسط یا انتهای خطوط) آیدی ایموجی پریمیوم (اعداد ۱۵ تا ۲۲ رقمی) ببیند،
    آن را به تگ استاندارد HTML تلگرام تبدیل می‌کند تا در متن بنر کاملاً درست نمایش داده شود.
    """
    return re.sub(r'(\d{15,22})', r"<tg-custom-emoji emoji-id='\1'>✨</tg-custom-emoji>", text)

def extract_name_and_emoji(text):
    match = re.search(r'(\d{15,22})', text)
    emoji_id = match.group(1) if match else None
    name = re.sub(r'\d{15,22}', '', text).strip()
    return name if name else "دکمه", emoji_id

async def get_channel_info(session):
    if not CHANNEL_ID: return "تنظیم نشده", "https://t.me/telegram"
    res = await api_request(session, "getChat", {"chat_id": CHANNEL_ID})
    if res and res.get("ok"):
        return res["result"]["title"], res["result"].get("invite_link", f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    return "عضویت در کانال", f"https://t.me/{CHANNEL_ID.replace('@', '')}"

async def check_user_joined(session, user_id):
    if not CHANNEL_ID: return True
    res = await api_request(session, "getChatMember", {"chat_id": CHANNEL_ID, "user_id": user_id})
    if res and res.get("ok"):
        return res["result"]["status"] in ["member", "administrator", "creator"]
    return False

def parse_timer_to_seconds(time_str):
    text = convert_persian_to_english_digits(time_str)
    nums = re.findall(r'\d+', text)
    if not nums: return None
    val = int(nums[0])
    if "دقیقه" in text: return val * 60
    if "ساعت" in text: return val * 3600
    if "روز" in text: return val * 86400
    return val * 60

async def send_start_message(session, chat_id):
    channel_title, channel_url = await get_channel_info(session)
    if not channel_url: channel_url = "https://t.me/telegram"
        
    text = "<tg-custom-emoji emoji-id='5019617635629794161'>⭐️</tg-custom-emoji> برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید، سپس روی دکمه «<tg-custom-emoji emoji-id='5206607081334906820'>✅</tg-custom-emoji> تأیید عضویت» کلیک کنید."
    reply_markup = {
        "inline_keyboard": [
            [{"text": channel_title, "url": channel_url}],
            [{"text": "تأیید عضویت", "callback_data": "verify_join", "icon_custom_emoji_id": "5206607081334906820"}]
        ]
    }
    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup})

async def send_main_menu(session, chat_id, user_id, text_message="خوش امدین به ربات ارسال بنر خودکار"):
    keyboard = [
        [{"text": "تنظیم بنر"}, {"text": "تنظیم چنل"}],
        [{"text": "دکمه شیشه ای"}, {"text": "تنظیم تایم"}],
        [{"text": "اطلاعات من"}, {"text": "پشتیبانی"}]
    ]
    if OWNER_ID != 0 and user_id == OWNER_ID:
        keyboard.append([{"text": "وارد کردن شماره چکر"}])
        
    reply_markup = {"keyboard": keyboard, "resize_keyboard": True}
    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": text_message, "reply_markup": reply_markup})

# =================================================================
# هوش مصنوعی استارز و پریمیوم (با وقفه ۱۰ ثانیه‌ای بین استعلام‌ها)
# =================================================================
async def get_live_price_from_group_stars(app, star_amount, profit_percent):
    sent_msg = await app.send_message(GROUP_ID, f"{star_amount} استارز")
    price_found = None
    for _ in range(10):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(GROUP_ID, limit=5):
            if msg.from_user and msg.from_user.username == CHECKER_BOT_USERNAME and msg.reply_to_message_id == sent_msg.id:
                match = re.search(r'💶\s*([\d,]+)\s*toman', msg.text, re.IGNORECASE)
                if match:
                    raw_price = int(match.group(1).replace(",", ""))
                    final_price = int(raw_price + (raw_price * profit_percent / 100))
                    price_found = f"{final_price:,}"
                    break
        if price_found: break
    return price_found

async def get_live_price_from_group_premium(app, profit_percent):
    sent_msg = await app.send_message(GROUP_ID, "پریمیوم")
    prices = {}
    for _ in range(10):
        await asyncio.sleep(1)
        async for msg in app.get_chat_history(GROUP_ID, limit=5):
            if msg.from_user and msg.from_user.username == CHECKER_BOT_USERNAME and msg.reply_to_message_id == sent_msg.id:
                m3 = re.search(r'3\s*ماهه.*?💶\s*([\d,]+)\s*تومن', msg.text, re.DOTALL)
                m6 = re.search(r'6\s*ماهه.*?💶\s*([\d,]+)\s*تومن', msg.text, re.DOTALL)
                m12 = re.search(r'1\s*ساله.*?💶\s*([\d,]+)\s*تومن', msg.text, re.DOTALL)
                
                if m3: prices["3"] = f"{int(int(m3.group(1).replace(',', '')) * (1 + profit_percent / 100)):,}"
                if m6: prices["6"] = f"{int(int(m6.group(1).replace(',', '')) * (1 + profit_percent / 100)):,}"
                if m12: prices["12"] = f"{int(int(m12.group(1).replace(',', '')) * (1 + profit_percent / 100)):,}"
                break
        if prices: break
    return prices

async def ai_update_banner_prices_async(banner_text, user_data_obj):
    client_data = user_data_obj.get("checker")
    if not client_data or "session_string" not in client_data: 
        return banner_text

    app = Client(f"checker_temp_{user_data_obj['_id']}", api_id=client_data["api_id"], api_hash=client_data["api_hash"], session_string=client_data["session_string"], in_memory=True)
    await app.start()

    result_text = banner_text
    
    # 1. پردازش هوشمند استارز در هر کجای متن (تشخیص دقیق 50 تا، 100 تا و غیره)
    stars_pattern = r'(\d+)\s*تا:\s*([\d,]+)\s*تومان'
    if re.search(stars_pattern, result_text):
        matches = list(re.finditer(stars_pattern, result_text))
        profit_percent = user_data_obj.get("stars_profit", 20.0)
        
        for match in matches:
            full_match = match.group(0)
            star_count = match.group(1)
            old_price = match.group(2)
            
            new_price = await get_live_price_from_group_stars(app, star_count, profit_percent)
            if new_price:
                new_str = f"{star_count} تا: {new_price} تومان"
                result_text = result_text.replace(full_match, new_str)
            
            await asyncio.sleep(10) # 10 ثانیه فاصله بین هر استعلام برای جلوگیری از ریپورت شدن اکانت چکر

    # 2. پردازش پریمیوم
    prem_pattern_3 = r'((?:۳|3)\s*ماهه[^:]*:\s*)([\d,]+)(\s*تومان)'
    prem_pattern_6 = r'((?:۶|6)\s*ماهه[^:]*:\s*)([\d,]+)(\s*تومان)'
    prem_pattern_12 = r'((?:۱|1)\s*(?:ساله|سال)[^:]*:\s*)([\d,]+)(\s*تومان)'
    
    if re.search(prem_pattern_3, result_text) or re.search(prem_pattern_6, result_text) or re.search(prem_pattern_12, result_text):
        profit_percent = user_data_obj.get("premium_profit", 20.0)
        prem_prices = await get_live_price_from_group_premium(app, profit_percent)
        if prem_prices:
            if "3" in prem_prices: result_text = re.sub(prem_pattern_3, r'\g<1>' + prem_prices["3"] + r'\g<3>', result_text)
            if "6" in prem_prices: result_text = re.sub(prem_pattern_6, r'\g<1>' + prem_prices["6"] + r'\g<3>', result_text)
            if "12" in prem_prices: result_text = re.sub(prem_pattern_12, r'\g<1>' + prem_prices["12"] + r'\g<3>', result_text)
                
    await app.stop()
    return result_text

# =================================================================
# ارسال اتوماتیک (شروع ۵ دقیقه زودتر برای بروزرسانی قیمت‌ها)
# =================================================================
async def background_poster():
    async with aiohttp.ClientSession() as session:
        while True:
            current_timestamp = int(time.time())
            all_users = await get_all_users()
            
            for user in all_users:
                banners = user.get("banners", {})
                auto_delete = user.get("auto_delete", False)
                user_id = user["_id"]
                banners_updated = False
                
                for banner_name, banner_info in banners.items():
                    timer_str = banner_info.get("timer")
                    if not timer_str: continue
                    
                    interval = parse_timer_to_seconds(timer_str)
                    if not interval or interval < 300: interval = 300 # حداقل ۵ دقیقه
                        
                    last_posted = banner_info.get("last_posted_timestamp", 0)
                    
                    # ۵ دقیقه زودتر (300 ثانیه زودتر) فرایند استعلام قیمت شروع می‌شود
                    pre_fetch_time = interval - 300
                    if pre_fetch_time < 0: pre_fetch_time = 0
                    
                    if current_timestamp - last_posted >= pre_fetch_time:
                        banner_info["last_posted_timestamp"] = current_timestamp
                        banners_updated = True
                        
                        original_content = banner_info.get("content", "")
                        inline_keyboard = banner_info.get("keyboard", [])
                        
                        # هوش مصنوعی قیمت‌ها را به‌روز می‌کند
                        smart_content = await ai_update_banner_prices_async(original_content, user)
                        final_content = format_custom_emojis(smart_content)
                        
                        last_msg_id = banner_info.get("last_message_id")
                        if auto_delete and last_msg_id:
                            await api_request(session, "deleteMessage", {"chat_id": CHANNEL_ID, "message_id": last_msg_id})
                        
                        payload = {"chat_id": CHANNEL_ID, "text": final_content, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": inline_keyboard} if inline_keyboard else None}
                        res = await api_request(session, "sendMessage", payload)
                        if res and res.get("ok"):
                            banner_info["last_message_id"] = res["result"]["message_id"]
                            
                if banners_updated:
                    await update_user_data(user_id, {"banners": banners})
            
            await asyncio.sleep(30)

# =================================================================
# حلقه اصلی ربات
# =================================================================
async def main_bot_loop():
    offset = None
    
    async with aiohttp.ClientSession() as session:
        print("🚀 ربات آماده دریافت پیام‌هاست...")
        await api_request(session, "deleteWebhook", {"drop_pending_updates": True})
        
        while True:
            try:
                updates = await api_request(session, "getUpdates", {"offset": offset, "timeout": 50})
                if updates and updates.get("ok"):
                    for update in updates["result"]:
                        offset = update["update_id"] + 1
                        
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            user_id = update["message"]["from"]["id"]
                            text = update["message"]["text"]
                            
                            u_data = await get_user_data(user_id)
                            state = user_states.get(user_id, {}).get("state")
                            
                            if text == "/start":
                                user_states.pop(user_id, None)
                                is_joined = await check_user_joined(session, user_id)
                                if is_joined:
                                    await send_main_menu(session, chat_id, user_id)
                                else:
                                    await send_start_message(session, chat_id)
                                    
                            elif text == "تنظیم چنل":
                                user_states[user_id] = {"state": "waiting_for_channel_link"}
                                reply_markup = {"inline_keyboard": [[{"text": "تنظیم", "callback_data": "start_setting_channel"}]]}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "کاربر گرامی چنل خود را با استفاده از دکمه زیر تنظیم کنید", "reply_markup": reply_markup})

                            elif text == "تنظیم بنر":
                                reply_markup = {"inline_keyboard": [[{"text": "تنظیم بنر", "callback_data": "start_setting_banner_name", "icon_custom_emoji_id": "5444856076954520455"}, {"text": "لغو و بازگشت", "callback_data": "cancel_action", "icon_custom_emoji_id": "5787292363470672097"}]]}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "کاربر گرامی وقتی بنر خود را ارسال میکنید با ایدی ایموجی ارسال کنید تا به درستی بنر شما در چنل مد نظر تنظیم بشه", "reply_markup": reply_markup})
                                
                            elif text == "تنظیم تایم":
                                banners = list(u_data.get("banners", {}).keys())
                                if not banners:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "❌ ابتدا بنر تنظیم کنید."})
                                else:
                                    keyboard = [[{"text": b, "callback_data": f"select_time_banner_{i}"}] for i, b in enumerate(banners)]
                                    keyboard.append([{"text": "بازگشت", "callback_data": "cancel_action"}])
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "لیست بنرهای شما:", "reply_markup": {"inline_keyboard": keyboard}})

                            elif text == "دکمه شیشه ای":
                                banners = list(u_data.get("banners", {}).keys())
                                if not banners:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "❌ ابتدا بنر بسازید!"})
                                else:
                                    text_msg = "کاربر گرامی به بخش اضافه کردن دکمه شیشه ای به بنر خود خوش امدید <tg-custom-emoji emoji-id='5296349143084595007'>✨</tg-custom-emoji>\nروی دکمه‌ بنر خود کلیک‌ نمایید"
                                    keyboard = [[{"text": b, "callback_data": f"select_inlineb_{i}"}] for i, b in enumerate(banners)]
                                    keyboard.append([{"text": "بازگشت", "callback_data": "cancel_action"}])
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": text_msg, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": keyboard}})

                            elif text == "اطلاعات من":
                                keyboard = [
                                    [{"text": "تنظیمات", "callback_data": "prof_settings"}],
                                    [{"text": "بنر ها", "callback_data": "prof_banners"}],
                                    [{"text": "دکمه شیشه ای ها", "callback_data": "prof_inline_btns"}],
                                    [{"text": "تایمر ها", "callback_data": "prof_timers"}],
                                    [{"text": "بازگشت", "callback_data": "cancel_action"}]
                                ]
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "اطلاعات من:", "reply_markup": {"inline_keyboard": keyboard}})

                            elif text == "پشتیبانی":
                                keyboard = [
                                    [{"text": "@Silverrmb", "url": "https://t.me/Silverrmb"}],
                                    [{"text": "@ID_KASEB", "url": "https://t.me/ID_KASEB"}],
                                    [{"text": "بستن", "callback_data": "cancel_action"}]
                                ]
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "پشتیبانی مورد نظر را کلیک نمایید", "reply_markup": {"inline_keyboard": keyboard}})
                                
                            elif text == "وارد کردن شماره چکر":
                                if OWNER_ID != 0 and user_id == OWNER_ID:
                                    user_states[user_id] = {"state": "checker_api_id"}
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "لطفاً API ID اکانت چکر را ارسال نمایید:"})
                                    
                            elif text in ["تنظیم سود استارز", "تنظیم سود پریمیوم"]:
                                if text == "تنظیم سود استارز":
                                    user_states[user_id] = {"state": "waiting_for_stars_profit"}
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "سود استارز را اعمال کنید مثال (۲۰):"})
                                else:
                                    user_states[user_id] = {"state": "waiting_for_premium_profit"}
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "سود پریمیوم را اعمال کنید مثال (۲۰):"})
                                
                            elif state == "waiting_for_stars_profit":
                                profit_str = convert_persian_to_english_digits(text.replace("درصد", "").replace("%", "").strip())
                                await update_user_data(user_id, {"stars_profit": float(profit_str)})
                                user_states.pop(user_id, None)
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"✅ سود استارز شما روی {profit_str} درصد تنظیم شد."})
                                
                            elif state == "waiting_for_premium_profit":
                                profit_str = convert_persian_to_english_digits(text.replace("درصد", "").replace("%", "").strip())
                                await update_user_data(user_id, {"premium_profit": float(profit_str)})
                                user_states.pop(user_id, None)
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"✅ سود پریمیوم شما روی {profit_str} درصد تنظیم شد."})

                            elif state == "checker_api_id":
                                user_states[user_id]["temp_api_id"] = text.strip()
                                user_states[user_id]["state"] = "checker_api_hash"
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "لطفاً API HASH خود را ارسال نمایید:"})
                            
                            elif state == "checker_api_hash":
                                user_states[user_id]["temp_api_hash"] = text.strip()
                                user_states[user_id]["state"] = "checker_phone"
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "لطفاً شماره موبایل اکانت چکر را با کد کشور ارسال کنید:"})
                                
                            elif state == "checker_phone":
                                phone = text.strip()
                                api_id = int(user_states[user_id]["temp_api_id"])
                                api_hash = user_states[user_id]["temp_api_hash"]
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "در حال اتصال به تلگرام و ارسال کد..."})
                                
                                client = Client(f"checker_temp_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
                                await client.connect()
                                sent_code = await client.send_code(phone)
                                temp_login_clients[user_id] = {"client": client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash, "api_id": api_id, "api_hash": api_hash}
                                user_states[user_id]["state"] = "checker_code"
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "✅ کد ورود ارسال شد. لطفاً کد را اینجا ارسال کنید:"})
                                
                            elif state == "checker_code":
                                login_code = convert_persian_to_english_digits(text.strip())
                                login_data = temp_login_clients.get(user_id)
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "🔄 در حال لاگین..."})
                                try:
                                    client = login_data["client"]
                                    await client.sign_in(login_data["phone"], login_data["phone_code_hash"], login_code)
                                    session_string = await client.export_session_string()
                                    await client.disconnect()
                                    
                                    checker_dict = {"api_id": login_data["api_id"], "api_hash": login_data["api_hash"], "session_string": session_string}
                                    await update_user_data(user_id, {"checker": checker_dict})
                                    
                                    user_states.pop(user_id, None)
                                    temp_login_clients.pop(user_id, None)
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "🎉 اکانت چکر متصل شد."})
                                except Exception as e:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"❌ خطا در کد: {e}"})

                            elif state == "waiting_for_channel_link":
                                user_states[user_id]["temp_channel"] = text.strip()
                                user_states[user_id]["state"] = "waiting_for_confirmation"
                                reply_markup = {"inline_keyboard": [[{"text": "تایید", "callback_data": "confirm_channel", "icon_custom_emoji_id": "5852871561983299073"}, {"text": "لغو عملیات", "callback_data": "cancel_action", "icon_custom_emoji_id": "5852812849780362931"}]]}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"کاربر گرامی چنل شما {text.strip()} تایید است ؟", "reply_markup": reply_markup})

                            elif state == "waiting_for_banner_name":
                                user_states[user_id]["temp_banner_name"] = text.strip()
                                user_states[user_id]["state"] = "waiting_for_banner_content"
                                reply_markup = {"inline_keyboard": [[{"text": "بازگشت", "callback_data": "start_setting_banner_name", "icon_custom_emoji_id": "5787292363470672097"}]]}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "بنر همراه با ایدی ایموجی ها ارسال کنید", "reply_markup": reply_markup})

                            elif state == "waiting_for_banner_content":
                                user_states[user_id]["temp_banner_content"] = text.strip()
                                user_states[user_id]["state"] = "waiting_for_banner_confirmation"
                                preview_text = format_custom_emojis(text.strip())
                                reply_markup = {"inline_keyboard": [[{"text": "تایید بنر", "callback_data": "confirm_banner", "icon_custom_emoji_id": "521293227537675960"}], [{"text": "بازگشت", "callback_data": "cancel_action", "icon_custom_emoji_id": "5787292363470672097"}]]}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"پیش‌نمایش بنر:\n\n{preview_text}", "parse_mode": "HTML", "reply_markup": reply_markup})

                            elif state == "waiting_for_time_input":
                                idx = user_states[user_id].get("selected_time_banner_idx")
                                if idx is not None:
                                    b_name = list(u_data["banners"].keys())[idx]
                                    u_data["banners"][b_name]["timer"] = text.strip()
                                    await update_user_data(user_id, {"banners": u_data["banners"]})
                                user_states.pop(user_id, None) 
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "تایم با موفقیت تنظیم شد <tg-custom-emoji emoji-id='5852871561983299073'>✅</tg-custom-emoji>", "parse_mode": "HTML"})
                                await asyncio.sleep(0.5)
                                await send_main_menu(session, chat_id, user_id)

                            elif state in ["waiting_for_inline_btn_name", "waiting_for_subsequent_btn_name"]:
                                btn_name, emoji_id = extract_name_and_emoji(text)
                                new_btn = {"text": btn_name, "callback_data": "dummy"}
                                if emoji_id: new_btn["icon_custom_emoji_id"] = emoji_id
                                
                                layout = user_states[user_id].get("temp_inline_layout", [])
                                if not layout:
                                    layout.append([new_btn])
                                    user_states[user_id]["temp_inline_layout"] = layout
                                    keyboard = [[{"text": "بله", "callback_data": "inline_continue_yes", "icon_custom_emoji_id": "5852871561983299073"}, {"text": "خیر", "callback_data": "inline_continue_no", "icon_custom_emoji_id": "5852812849780362931"}]]
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "دکمه تایید شد. آیا میخواهید دکمه دیگری اضافه کنید؟", "reply_markup": {"inline_keyboard": keyboard}})
                                else:
                                    user_states[user_id]["temp_new_btn"] = new_btn
                                    user_states[user_id]["state"] = "waiting_for_inline_direction"
                                    keyboard = [[{"text": "بالا", "callback_data": "btndir_top"}],
                                                [{"text": "چپ", "callback_data": "btndir_left"}, {"text": "راست", "callback_data": "btndir_right"}],
                                                [{"text": "پایین", "callback_data": "btndir_bottom"}]]
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "جهت دکمه را تنظیم کنید", "reply_markup": {"inline_keyboard": keyboard}})
                                
                        # ----------------- دکمه‌های شیشه‌ای (کال‌بک‌ها) -----------------
                        elif "callback_query" in update:
                            query = update["callback_query"]
                            query_id = query["id"]
                            user_id = query["from"]["id"]
                            chat_id = query["message"]["chat"]["id"]
                            message_id = query["message"]["message_id"]
                            data = query["data"]
                            
                            u_data = await get_user_data(user_id)
                            
                            if data == "verify_join":
                                if await check_user_joined(session, user_id):
                                    await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                    await send_main_menu(session, chat_id, user_id)
                                    await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                else:
                                    await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id, "text": "❌ هنوز جوین نیستید!", "show_alert": True})

                            elif data == "cancel_action":
                                user_states.pop(user_id, None)
                                await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                await send_main_menu(session, chat_id, user_id, "❌ لغو شد.")
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "start_setting_channel":
                                user_states[user_id] = {"state": "waiting_for_channel_link"}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "لینک چنل خود را ارسال نمایید\nمثال : https://t.me/Rhino_botTM"})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "confirm_channel":
                                channel_link = user_states.get(user_id, {}).get("temp_channel", "شما")
                                reply_markup = {"inline_keyboard": [[{"text": "ادمین شد", "callback_data": "admin_done", "icon_custom_emoji_id": "6028565819225542441"}]]}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": f"کاربر گرامی ربات را در چنل {channel_link} ادمین کنید و دسترسی های : پست گزاشتن، ویرایش پست، حذف پست، را برای ربات ازاد کنید", "reply_markup": reply_markup})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "admin_done":
                                user_states.pop(user_id, None)
                                await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                await send_main_menu(session, chat_id, user_id, "تایید شد")
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "start_setting_banner_name":
                                user_states[user_id] = {"state": "waiting_for_banner_name"}
                                reply_markup = {"inline_keyboard": [[{"text": "بازگشت", "callback_data": "cancel_action", "icon_custom_emoji_id": "5444856076954520455"}]]}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "کاربر گرامی اسم برای بنر خود انتخاب کنید", "reply_markup": reply_markup})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "confirm_banner":
                                banner_name = user_states.get(user_id, {}).get("temp_banner_name", "بنر")
                                banner_content = user_states.get(user_id, {}).get("temp_banner_content", "")
                                u_data["banners"][banner_name] = {"content": banner_content, "keyboard": []}
                                await update_user_data(user_id, {"banners": u_data["banners"]})
                                user_states.pop(user_id, None)
                                reply_markup = {"inline_keyboard": [[{"text": "چنل من", "callback_data": "cancel_action"}]]}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "چنل مورد نظر را انتخاب کنید", "parse_mode": "HTML", "reply_markup": reply_markup})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data.startswith("select_time_banner_"):
                                idx = int(data.split("_")[-1])
                                user_states[user_id] = {"state": "waiting_for_time_input", "selected_time_banner_idx": idx}
                                text = "کاربر گرامی تایم ارسال بنر در چنل مورد نظر را انتخاب کنید\nمثال: 24 ساعت\nمثال : 30 دقیقه\nکمترین تایم برای بنر 5 دقیقه و بیشترین تایم 144 ساعت یعنی 6 روز میباشد"
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": {"inline_keyboard": [[{"text": "بازگشت", "callback_data": "cancel_action"}]]}})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data.startswith("select_inlineb_"):
                                idx = int(data.split("_")[-1])
                                b_name = list(u_data["banners"].keys())[idx]
                                user_states[user_id] = {"state": "waiting_for_inline_btn_name", "selected_banner": b_name, "temp_inline_layout": []}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "اسم و ایدی ایموجی برای دکمه شیشه‌ای را ارسال نمایید ✨", "reply_markup": {"inline_keyboard": [[{"text": "بازگشت", "callback_data": "cancel_action"}]]}})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                
                            elif data.startswith("btndir_"):
                                direction = data.split("_")[-1]
                                new_btn = user_states[user_id]["temp_new_btn"]
                                layout = user_states[user_id]["temp_inline_layout"]
                                
                                if direction == "top": layout.insert(0, [new_btn])
                                elif direction == "bottom": layout.append([new_btn])
                                elif direction == "left": layout[-1].insert(0, new_btn)
                                elif direction == "right": layout[-1].append(new_btn)
                                
                                keyboard = [[{"text": "بله", "callback_data": "inline_continue_yes", "icon_custom_emoji_id": "5852871561983299073"}, {"text": "خیر", "callback_data": "inline_continue_no", "icon_custom_emoji_id": "5852812849780362931"}]]
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "جهت تایید شد. آیا میخواهید دکمه دیگری اضافه کنید؟", "reply_markup": {"inline_keyboard": keyboard}})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                
                            elif data == "inline_continue_yes":
                                user_states[user_id]["state"] = "waiting_for_subsequent_btn_name"
                                text = "اسم و ایدی ایموجی برای دکمه دوم را ارسال نمایید <tg-custom-emoji emoji-id='5296480809602023717'>✨</tg-custom-emoji>"
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "inline_continue_no":
                                banner_name = user_states[user_id].get("selected_banner")
                                final_layout = user_states[user_id]["temp_inline_layout"]
                                if banner_name in u_data["banners"]:
                                    u_data["banners"][banner_name]["keyboard"] = final_layout
                                    await update_user_data(user_id, {"banners": u_data["banners"]})
                                user_states.pop(user_id, None)
                                await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                await send_main_menu(session, chat_id, user_id, "✅ عملیات ساخت دکمه شیشه‌ای تمام شد.")
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

            except Exception as e:
                print("Error in polling loop:", e)
                await asyncio.sleep(2)

async def run_all():
    db_connected = await init_db()
    if db_connected:
        await asyncio.gather(main_bot_loop(), background_poster())

if __name__ == "__main__":
    asyncio.run(run_all())
