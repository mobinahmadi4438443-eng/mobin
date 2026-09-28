import os
import asyncio
import re
import aiohttp
from datetime import datetime
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient

# =================================================================
# دریافت متغیرهای محیطی از Railway
# =================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MONGO_URI = os.getenv("MONGO_URI")

# متغیرهای اختیاری برای لاگین ربات‌های چکر
# این موارد را هم در Railway تنظیم کنید تا ربات بتواند کلاینت‌ها را بسازد
API_ID = int(os.getenv("API_ID", 1234567)) 
API_HASH = os.getenv("API_HASH", "your_api_hash_here")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
GROUP_ID = -1004426176128
CHECKER_BOT_USERNAME = "HashTrxCheckerBot"

# =================================================================
# اتصال به دیتابیس MongoDB (سرعت بالا و غیرهمزمان)
# =================================================================
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.telegram_bot
users_collection = db.users

# وضعیت‌های موقت در حافظه رم (برای سرعت بیشتر)
user_states = {}
temp_login_clients = {}

# --- توابع دیتابیس ---
async def get_user_data(user_id):
    """دریافت اطلاعات کاربر از دیتابیس"""
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "banners": {}, "auto_delete": False, "stars_profit": 20.0, "premium_profit": 20.0}
        await users_collection.insert_one(user)
    return user

async def update_user_data(user_id, update_dict):
    """بروزرسانی اطلاعات کاربر در دیتابیس"""
    await users_collection.update_one({"_id": user_id}, {"$set": update_dict}, upsert=True)

# =================================================================
# توابع پایه و درخواست‌ها
# =================================================================
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
# هوش مصنوعی استارز و پریمیوم (متصل به دیتابیس)
# =================================================================
async def get_live_price_from_group_stars(user_data, star_amount):
    client_data = user_data.get("checker")
    if not client_data or "session_string" not in client_data: return None

    app = Client(f"checker_temp_{user_data['_id']}", api_id=client_data["api_id"], api_hash=client_data["api_hash"], session_string=client_data["session_string"], in_memory=True)
    await app.start()
    sent_msg = await app.send_message(GROUP_ID, f"{star_amount} استارز")
    
    price_found = None
    profit_percent = user_data.get("stars_profit", 20.0)
    
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

async def get_live_price_from_group_premium(user_data):
    client_data = user_data.get("checker")
    if not client_data or "session_string" not in client_data: return None

    app = Client(f"checker_temp_{user_data['_id']}_prem", api_id=client_data["api_id"], api_hash=client_data["api_hash"], session_string=client_data["session_string"], in_memory=True)
    await app.start()
    sent_msg = await app.send_message(GROUP_ID, "پریمیوم")
    
    prices = {}
    profit_percent = user_data.get("premium_profit", 20.0)
    
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

async def ai_update_banner_prices_async(banner_text, user_data):
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
            
            new_price = await get_live_price_from_group_stars(user_data, star_count)
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
        prem_prices = await get_live_price_from_group_premium(user_data)
        if prem_prices:
            if "3" in prem_prices: result_text = re.sub(prem_pattern_3, r'\g<1>' + prem_prices["3"] + r'\g<3>', result_text)
            if "6" in prem_prices: result_text = re.sub(prem_pattern_6, r'\g<1>' + prem_prices["6"] + r'\g<3>', result_text)
            if "12" in prem_prices: result_text = re.sub(prem_pattern_12, r'\g<1>' + prem_prices["12"] + r'\g<3>', result_text)
                
    return result_text

# =================================================================
# ارسال اتوماتیک سر تایم (Background Task خواندن از دیتابیس)
# =================================================================
async def background_poster():
    async with aiohttp.ClientSession() as session:
        while True:
            now_time = datetime.now().strftime("%H:%M")
            # دریافت تمامی کاربران از دیتابیس
            async for user in users_collection.find({}):
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
                            
                # اگر تغییری در بنرها (آیدی پیام جدید یا تایم آخرین پست) ایجاد شد در دیتابیس ذخیره کن
                if banners_updated:
                    await update_user_data(user_id, {"banners": banners})
            
            await asyncio.sleep(30)

# =================================================================
# حلقه اصلی ربات (Long Polling)
# =================================================================
async def main_bot_loop():
    offset = None
    print("ربات روشن شد و به دیتابیس MongoDB متصل است...")
    
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
                            
                            # لود کردن دیتای کاربر از دیتابیس
                            u_data = await get_user_data(user_id)
                            state = user_states.get(user_id, {}).get("state")
                            
                            if text == "/start":
                                user_states.pop(user_id, None)
                                await send_start_message(session, chat_id)
                                
                            elif text == "تنظیم سود استارز":
                                user_states[user_id] = {"state": "waiting_for_stars_profit"}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "سود را اعمال کنید مثال (۲۰):"})
                            elif text == "تنظیم سود پریمیوم":
                                user_states[user_id] = {"state": "waiting_for_premium_profit"}
                                await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "سود را اعمال کنید مثال (۲۰):"})
                                
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
                                    
                                    # ذخیره سشن در دیتابیس
                                    checker_dict = {"api_id": login_data["api_id"], "api_hash": login_data["api_hash"], "session_string": session_string}
                                    await update_user_data(user_id, {"checker": checker_dict})
                                    
                                    user_states.pop(user_id, None)
                                    temp_login_clients.pop(user_id, None)
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": "🎉 اکانت چکر با موفقیت متصل شد و در دیتابیس ذخیره گردید."})
                                except Exception as e:
                                    await api_request(session, "sendMessage", {"chat_id": chat_id, "text": f"❌ خطا در کد: {e}"})

                        # ----------------- دکمه‌های شیشه‌ای -----------------
                        elif "callback_query" in update:
                            query = update["callback_query"]
                            query_id = query["id"]
                            user_id = query["from"]["id"]
                            chat_id = query["message"]["chat"]["id"]
                            message_id = query["message"]["message_id"]
                            data = query["data"]
                            
                            u_data = await get_user_data(user_id)
                            
                            if data == "menu_profile":
                                keyboard = [
                                    [{"text": "تنظیمات", "callback_data": "prof_settings", "style": "primary"}],
                                    [{"text": "بنر ها", "callback_data": "prof_banners", "style": "primary"}],
                                    [{"text": "تایمر ها", "callback_data": "prof_timers", "style": "primary"}],
                                    [{"text": "افزودن چکر (هوش مصنوعی)", "callback_data": "prof_add_checker", "style": "success"}],
                                    [{"text": "بازگشت", "callback_data": "cancel_action", "style": "danger"}]
                                ]
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "بخش اطلاعات من (تنظیم سود: «تنظیم سود استارز» یا «تنظیم سود پریمیوم»):", "reply_markup": {"inline_keyboard": keyboard}})
                                await api_request(session, "answerCallbackQuery", {"callback_query_id": query_id})
                                
                            elif data == "prof_add_checker":
                                user_states[user_id] = {"state": "checker_api_id"}
                                await api_request(session, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": "لطفاً API ID خود را ارسال نمایید:"})
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
    await asyncio.gather(main_bot_loop(), background_poster())

if __name__ == "__main__":
    asyncio.run(run_all())
