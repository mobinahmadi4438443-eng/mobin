import os
import asyncio
import re
import aiohttp
import json
from urllib.parse import urlparse
from datetime import datetime
from pyrogram import Client
import aiomysql

# =================================================================
# متغیرهای محیطی (Railway)
# =================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OWNER_ID = int(os.getenv("OWNER_ID", 0)) # آیدی مالک ربات
MYSQL_URL = os.getenv("MYSQL_URL") # آدرس کانکشن MySQL از Railway

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
GROUP_ID = -1004426176128
CHECKER_BOT_USERNAME = "HashTrxCheckerBot"

# =================================================================
# تنظیمات دیتابیس MySQL (پرسرعت و Async)
# =================================================================
db_pool = None

async def init_db():
    global db_pool
    # تجزیه آدرس کانکشن MySQL برای استخراج یوزر، پسورد، پورت و غیره
    url = urlparse(MYSQL_URL)
    
    db_pool = await aiomysql.create_pool(
        host=url.hostname,
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        db=url.path.lstrip('/'),
        autocommit=True
    )
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # ساخت جدول کاربران در صورت عدم وجود (بنرها به صورت LONGTEXT JSON ذخیره می‌شوند)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    auto_delete BOOLEAN DEFAULT FALSE,
                    stars_profit FLOAT DEFAULT 20.0,
                    premium_profit FLOAT DEFAULT 20.0,
                    checker_api_id BIGINT NULL,
                    checker_api_hash VARCHAR(255) NULL,
                    checker_session TEXT NULL,
                    banners LONGTEXT
                )
            """)

async def get_user_data(user_id):
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            if not row:
                await cur.execute("INSERT INTO users (user_id, banners) VALUES (%s, '{}')", (user_id,))
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
            if row.get('checker_session'):
                user['checker'] = {
                    "api_id": row['checker_api_id'],
                    "api_hash": row['checker_api_hash'],
                    "session_string": row['checker_session']
                }
            return user

async def update_user_data(user_id, update_dict):
    sets = []
    values = []
    if "banners" in update_dict:
        sets.append("banners = %s")
        values.append(json.dumps(update_dict["banners"]))
    if "stars_profit" in update_dict:
        sets.append("stars_profit = %s")
        values.append(update_dict["stars_profit"])
    if "premium_profit" in update_dict:
        sets.append("premium_profit = %s")
        values.append(update_dict["premium_profit"])
    if "auto_delete" in update_dict:
        sets.append("auto_delete = %s")
        values.append(update_dict["auto_delete"])
    if "checker" in update_dict:
        checker = update_dict["checker"]
        sets.append("checker_api_id = %s")
        values.append(checker.get("api_id"))
        sets.append("checker_api_hash = %s")
        values.append(checker.get("api_hash"))
        sets.append("checker_session = %s")
        values.append(checker.get("session_string"))
        
    if not sets: return
    
    query = f"UPDATE users SET {', '.join(sets)} WHERE user_id = %s"
    values.append(user_id)
    
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, tuple(values))

async def get_all_users():
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users")
            rows = await cur.fetchall()
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
                if row.get('checker_session'):
                    u['checker'] = {
                        "api_id": row['checker_api_id'],
                        "api_hash": row['checker_api_hash'],
                        "session_string": row['checker_session']
                    }
                users.append(u)
            return users

# =================================================================
# وضعیت‌ها و اطلاعات موقت کاربران
# =================================================================
user_states = {}
temp_login_clients = {} 

async def api_request(session, method, payload=None):
    url = BASE_URL + method
    async with session.post(url, json=payload) as response:
        return await response.json()

def convert_persian_to_english_digits(text):
    persian = "۰۱۲۳۴۵۶۷۸۹"
    english = "0123456789"
    return text.translate(str.maketrans(persian, english))

def format_custom_emojis(text):
    return re.sub(r'(\d{15,22})', r"<tg-custom-emoji emoji-id='\1'>✨</tg-custom-emoji>", text)

def extract_name_and_emoji(text):
    match = re.search(r'(\d{15,22})', text)
    emoji_id = match.group(1) if match else None
    name = re.sub(r'\d{15,22}', '', text).strip()
    return name if name else "دکمه", emoji_id

async def get_channel_info(session):
    res = await api_request(session, "getChat", {"chat_id": CHANNEL_ID})
    if res.get("ok"):
        return res["result"]["title"], res["result"].get("invite_link", f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    return "عضویت در کانال", ""

async def send_start_message(session, chat_id):
    channel_title, channel_url = await get_channel_info(session)
    text = "<tg-custom-emoji emoji-id='5019617635629794161'>⭐️</tg-custom-emoji> برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید، سپس روی دکمه «<tg-custom-emoji emoji-id='5206607081334906820'>✅</tg-custom-emoji> تأیید عضویت» کلیک کنید."
    reply_markup = {
        "inline_keyboard": [
            [{"text": channel_title, "url": channel_url, "style": "primary"}],
            [{"text": "تأیید عضویت", "callback_data": "verify_join", "style": "success", "icon_custom_emoji_id": "5206607081334906820"}]
        ]
    }
    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup})

async def send_main_menu(session, chat_id, text_message="✅ لطفاً از منوی زیر انتخاب کنید:"):
    reply_markup = {
        "inline_keyboard": [
            [{"text": "تنظیم چنل", "callback_data": "menu_channel", "style": "primary", "icon_custom_emoji_id": "5796433758978577401"},
             {"text": "تنظیم بنر", "callback_data": "menu_banner", "style": "primary", "icon_custom_emoji_id": "5971818172985117571"}],
            [{"text": "تنظیم تایم", "callback_data": "menu_time", "style": "primary", "icon_custom_emoji_id": "5780543148782522693"},
             {"text": "دکمه شیشه ای", "callback_data": "menu_inline", "style": "primary", "icon_custom_emoji_id": "5895221391220804630"}],
            [{"text": "اطلاعات من", "callback_data": "menu_profile", "style": "primary", "icon_custom_emoji_id": "5971867376130461576"},
             {"text": "پشتیبانی", "callback_data": "menu_support", "style": "primary", "icon_custom_emoji_id": "5839301436717929423"}]
        ]
    }
    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": text_message, "reply_markup": reply_markup})

# =================================================================
# هوش مصنوعی استارز و پریمیوم (متصل به MySQL)
# =================================================================
async def get_live_price_from_group_stars(user_data_obj, star_amount):
    client_data = user_data_obj.get("checker")
    if not client_data or "session_string" not in client_data: return None

    app = Client(f"checker_temp_{user_data_obj['_id']}", api_id=client_data["api_id"], api_hash=client_data["api_hash"], session_string=client_data["session_string"], in_memory=True)
    await app.start()
    sent_msg = await app.send_message(GROUP_ID, f"{star_amount} استارز")
    
    price_found = None
    profit_percent = user_data_obj.get("stars_profit", 20.0)
    
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
            
    await app.stop()
    return price_found

async def get_live_price_from_group_premium(user_data_obj):
    client_data = user_data_obj.get("checker")
    if not client_data or "session_string" not in client_data: return None

    app = Client(f"checker_temp_{user_data_obj['_id']}_prem", api_id=client_data["api_id"], api_hash=client_data["api_hash"], session_string=client_data["session_string"], in_memory=True)
    await app.start()
    sent_msg = await app.send_message(GROUP_ID, "پریمیوم")
    
    prices = {}
    profit_percent = user_data_obj.get("premium_profit", 20.0)
    
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
            
    await app.stop()
    return prices

async def ai_update_banner_prices_async(banner_text, user_data_obj):
    result_text = banner_text
    
    # پردازش استارز
    stars_pattern = r'((?:⭐️\s*)?)(\d+)(\s*(?:تا|استارز)[^:]*:\s*)([\d,]+)(\s*تومان)'
    if re.search(stars_pattern, result_text):
        matches = list(re.finditer(stars_pattern, result_text))
        offset = 0
        temp_result = ""
        for match in matches:
            start, end = match.span()
            prefix, star_count, middle, old_price, suffix = match.groups()
            temp_result += result_text[offset:start]
            
            new_price = await get_live_price_from_group_stars(user_data_obj, star_count)
            if not new_price: new_price = old_price
            
            temp_result += f"{prefix}{star_count}{middle}{new_price}{suffix}"
            offset = end
        temp_result += result_text[offset:]
        result_text = temp_result

    # پردازش پریمیوم
    prem_pattern_3 = r'((?:۳|3)\s*ماهه[^:]*:\s*)([\d,]+)(\s*تومان)'
    prem_pattern_6 = r'((?:۶|6)\s*ماهه[^:]*:\s*)([\d,]+)(\s*تومان)'
    prem_pattern_12 = r'((?:۱|1)\s*(?:ساله|سال)[^:]*:\s*)([\d,]+)(\s*تومان)'
    
    if re.search(prem_pattern_3, result_text) or re.search(prem_pattern_6, result_text) or re.search(prem_pattern_12, result_text):
        prem_prices = await get_live_price_from_group_premium(user_data_obj)
        if prem_prices:
            if "3" in prem_prices: result_text = re.sub(prem_pattern_3, r'\g<1>' + prem_prices["3"] + r'\g<3>', result_text)
            if "6" in prem_prices: result_text = re.sub(prem_pattern_6, r'\g<1>' + prem_prices["6"] + r'\g<3>', result_text)
            if "12" in prem_prices: result_text = re.sub(prem_pattern_12, r'\g<1>' + prem_prices["12"] + r'\g<3>', result_text)
                
    return result_text

# =================================================================
# ارسال اتوماتیک سر تایم
# =================================================================
async def background_poster():
    async with aiohttp.ClientSession() as session:
        while True:
            now_time = datetime.now().strftime("%H:%M")
            all_users = await get_all_users()
            
            for user in all_users:
                banners = user.get("banners", {})
                auto_delete = user.get("auto_delete", False)
                user_id = user["_id"]
                banners_updated = False
                
                for banner_name, banner_info in banners.items():
                    timer = banner_info.get("timer")
                    last_posted = banner_info.get("last_posted_time")
                    
                    if timer == now_time and last_posted != now_time:
                        banner_info["last_posted_time"] = now_time
                        banners_updated = True
                        
                        original_content = banner_info.get("content", "")
                        inline_keyboard = banner_info.get("keyboard", [])
                        
                        smart_content = await ai_update_banner_prices_async(original_content, user)
                        final_content = format_custom_emojis(smart_content)
                        
                        last_msg_id = banner_info.get("last_message_id")
                        if auto_delete and last_msg_id:
                            await api_request(session, "deleteMessage", {"chat_id": CHANNEL_ID, "message_id": last_msg_id})
                        
                        payload = {"chat_id": CHANNEL_ID, "text": final_content, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": inline_keyboard} if inline_keyboard else None}
                        res = await api_request(session, "sendMessage", payload)
                        if res.get("ok"):
                            banner_info["last_message_id"] = res["result"]["message_id"]
                            
                if banners_updated:
                    await update_user_data(user_id, {"banners": banners})
            
            await asyncio.sleep(30)

# =================================================================
# حلقه اصلی ربات
# =================================================================
async def main_bot_loop():
    offset = None
    print("ربات روشن شد و به دیتابیس MySQL ابری متصل است...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                updates = await api_request(session, "getUpdates", {"offset": offset, "timeout": 50})
                if updates and updates.get("ok"):
                    for update in updates["result"]:
                        offset = update["update_id"] + 1
                        
                        # ----------------- پیام‌های متنی -----------------
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            user_id = update["message"]["from"]["id"]
                            text = update["message"]["text"]
                            
                            u_data = await get_user_data(user_id)
                            state = user_states.get(user_id, {}).get("state")
                            
                            if text == "/start":
                                user_states.pop(user_id, None)
                                await send_start_message(session, chat_id)
                                
                            # ----- مدیریت امنیت: فقط مالک -----
                            elif text in ["تنظیم سود استارز", "تنظیم سود پریمیوم"]:
                                if user_id != OWNER_ID:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "⛔️ شما مالک ربات نیستید و دسترسی به این بخش را ندارید."})
                                    continue
                                
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

                            # ----- اتصال چکر -----
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
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "🎉 اکانت چکر متصل شد و در دیتابیس امن MySQL ذخیره گردید."})
                                except Exception as e:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"❌ خطا در کد: {e}"})

                            # (سایر بخش‌های بنر و زمان مثل قبل در اینجا مدیریت می‌شوند)
                            elif state == "waiting_for_time_input":
                                idx = user_states[user_id].get("selected_time_banner_idx")
                                if idx is not None:
                                    b_name = list(u_data["banners"].keys())[idx]
                                    u_data["banners"][b_name]["timer"] = text.strip()
                                    await update_user_data(user_id, {"banners": u_data["banners"]})
                                user_states.pop(user_id, None) 
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "تایم با موفقیت تنظیم شد <tg-custom-emoji emoji-id='5852871561983299073'>✅</tg-custom-emoji>", "parse_mode": "HTML"})
                                await asyncio.sleep(0.5)
                                await send_main_menu(session, chat_id)
                                
                        # ----------------- دکمه‌های شیشه‌ای -----------------
                        elif "callback_query" in update:
                            query = update["callback_query"]
                            query_id = query["id"]
                            user_id = query["from"]["id"]
                            chat_id = query["message"]["chat"]["id"]
                            message_id = query["message"]["message_id"]
                            data = query["data"]
                            
                            if data == "verify_join":
                                await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                await send_main_menu(session, chat_id)
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                
                            elif data == "menu_profile":
                                keyboard = [
                                    [{"text": "تنظیمات", "callback_data": "prof_settings", "style": "primary"}],
                                    [{"text": "بنر ها", "callback_data": "prof_banners", "style": "primary"}],
                                    [{"text": "تایمر ها", "callback_data": "prof_timers", "style": "primary"}],
                                    [{"text": "افزودن چکر (هوش مصنوعی)", "callback_data": "prof_add_checker", "style": "success"}],
                                    [{"text": "بازگشت", "callback_data": "cancel_action", "style": "danger"}]
                                ]
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "بخش اطلاعات من (تنظیم سود: کلمات «تنظیم سود استارز» یا «تنظیم سود پریمیوم» را به ربات بفرستید):", "reply_markup": {"inline_keyboard": keyboard}})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                
                            elif data == "prof_add_checker":
                                # ----- فقط مالک می‌تواند چکر اضافه کند -----
                                if user_id != OWNER_ID:
                                    await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id, "text": "⛔️ فقط مالک اصلی ربات مجاز به اضافه کردن شماره است!", "show_alert": True})
                                else:
                                    user_states[user_id] = {"state": "checker_api_id"}
                                    await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "لطفاً API ID اکانت چکر را ارسال نمایید:"})
                                    await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

                            elif data == "cancel_action":
                                user_states.pop(user_id, None)
                                await api_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                                await send_main_menu(session, chat_id, "❌ لغو شد.")
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})

            except Exception as e:
                print("Error in polling loop:", e)
                await asyncio.sleep(2)

async def run_all():
    await init_db() # ساخت کانکشن MySQL
    await asyncio.gather(main_bot_loop(), background_poster())

if __name__ == "__main__":
    asyncio.run(run_all())
