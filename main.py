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
        "char1_name": "زولو", "char1_emoji": "5832457500821034730",
        "char2_name": "نورا", "char2_emoji": "5958487981772773271",
        "char3_name": "جسپر", "char3_emoji": "5780382873487939194",
        "char4_name": "رکس", "char4_emoji": "6034966544562265361"
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
# 🧩 دیتابیس عظیم ایموجی‌های پرمیوم شما
# ==========================================
# لیست شمشیرها و ضربات برای حمله
ATTACK_EMOJIS = [
    "5345906988301725409", "5343897957219477338", "5344032282321660839", "5343740353394551254", "5345939127541996538", 
    "5345800077975792172", "5343945962068946147", "5345801830322445591", "5339298412317680982", "5339480720794496201",
    "5339252847009634986", "5339142681098497146", "5339175846835953172", "5339384281598830250", "5337004109507634021",
    "5339441125490992832", "5958375350550403093", "5958490962480077066", "5958761283426719331", "5958376072104907832",
    "5958511380754601050", "5958372885239174716", "5958461262781225622", "5958816121569154412", "5958333805331748627",
    "5958594101824721885", "5958546676795840177", "5958701364337972534", "5958267186094020392", "5958665720404383923",
    "5958635874676643966", "5958609692556007137", "5958795840733583887", "5956169116044761371", "5958574052917384760",
    "5958621525190908249", "5958505857426659267", "5958804155790268495", "5958353600836015944", "5958578863280756877",
    "5958546861479434425", "5958487981772773271", "5958322028531423656", "5958643717286926603", "5958428071273961070",
    "5958762662111221332", "5956101388705470045", "5958281097493092896", "5956394859525837952", "5958746371300267640",
    "5956379642456708521", "5958473597927298471", "5958555236665660683", "5958581551930283817", "5958662262955711244",
    "5958378245358360456", "5958808141519919086", "5958786662388471763", "5958606630244325380", "5958618136461711872",
    "5958415641638607251", "5958624179480697023", "5958318313384711376", "5958816276187985125", "5958767927741126280"
]

# لیست انیمه‌های خشمگین و ترسناک (برای دراخور و آسیب دیدن)
BOSS_EMOJIS = [
    "6041846334846146779", "6041718654058374097", "6041988081651817010", "6042000747510373449", "6044381950393719705",
    "6041691913591986795", "6041794945562451034", "6044031657156025745", "6042067207834312047", "6044392984164702858",
    "6021493696011180326", "6021679199943665107", "6028251384669805758", "6021503011795245594", "6021683482026057273",
    "6021524963373098074", "6021527201051056472", "6021608144004716962", "6021653215391521041", "6021776476657949960",
    "6021628944531331852", "6021562582991640411", "6021324839371938222", "6021836374271860084", "6021339012764015617",
    "5783004749158685627", "5780556707994278784", "5782701868064971518", "5782913730211748145", "5780658176596646924",
    "5780609587631627157", "5780781407798305236", "5780585368311045618", "5780929133198450198", "5782843400122276474",
    "6037413112552889117", "6039679437945968043", "6039706547779541220", "5958808923203967006", "5958322028531423656",
    "5958487981772773271", "5780382873487939194", "5780765881491529111", "5829994341371747297", "6037163978679916501",
    "6034869770359152915", "6035078071978040145", "6037584997144074766", "6035097914726947384", "6034966544562265361",
    "6037095632865335166", "6037502439282712379", "6037533659399985698", "6037502185879641476", "6028251384669805758",
    "5814562360668461990", "5904551078094970096", "6039356525124787397", "6044381950393719705"
]

# لیست ایموجی‌های خون، شیلد و پیروزی (هیل کردن و محافظت)
HEAL_EMOJIS = [
    "5868727352879485936", "5868656266875769200", "5902141940744330810", "6028551194861899805", "6032699501909644905",
    "5902324558458789912", "5904341217402952011", "5902143499817458993", "6041761200004406848", "6041737710828264758",
    "6044320575311060640", "5814620926842511271", "5832631378277050554", "5807769659436440096", "5918119176135774001",
    "5857150470396581154", "5899781869100076644", "6037400103096948939", "6039877646391711784"
]

# ==========================================
# 🧩 سیستم خواندن و قالب‌بندی ایموجی‌ها
# ==========================================
async def get_emoji(btn_name: str, default_id: str):
    return await get_setting(f"emoji_{btn_name}", default_id)

def parse_emojis(text: str) -> str:
    return re.sub(r'(?<!["\'\d])(\d{15,22})(?!["\'\d])', r'<tg-emoji emoji-id="\1">✨</tg-emoji>', text)

def e(eid: str, fallback="✨") -> str:
    if not eid or not eid.strip().isdigit(): return fallback
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

def get_progress_bar(current: int, total: int, length: int, fill_id: str, empty_id: str) -> str:
    if total <= 0: total = 1
    filled = int((current / total) * length)
    if filled > length: filled = length
    if filled < 0: filled = 0
    empty = length - filled
    # استفاده از ایموجی ✨ مخفی به جای خط تیره تا تلگرام ارور ندهد
    return (f'<tg-emoji emoji-id="{fill_id}">✨</tg-emoji>' * filled) + (f'<tg-emoji emoji-id="{empty_id}">✨</tg-emoji>' * empty)

async def btn(text: str, cb_data: str, emoji_name: str, default_emoji: str):
    emoji_id = await get_emoji(emoji_name, default_emoji)
    button = {"text": text, "callback_data": cb_data}
    if emoji_id and str(emoji_id).strip().isdigit():
        button["icon_custom_emoji_id"] = str(emoji_id).strip()
    return button

# ==========================================
# 📝 متون ثابت و گرافیکی ربات
# ==========================================
MAIN_TEXT = parse_emojis("5282974228377789040 <b>منوی اصلی بازی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
GAME_MENU_TEXT = parse_emojis("5282974228377789040 <b>منوی داستانی تاتاروس</b>\n\n5019617635629794161 بخش مورد نظر خود را انتخاب کنید:")
CHAR_SELECTION_TEXT = parse_emojis("کاراکتر مورد نظر خودرا انتخاب کنید 5019617635629794161")

STORY_TEXT = parse_emojis(
    'سلام 5296480809602023717\n'
    'به بازی تاتاروس خوش آمدید 5296349143084595007\n\n'
    'با فشار دادن/کلیک کردن روی دکمه شروع وارد دنیای فراموش شده میشید.5303073678890662588\n\n'
    'دنیای فراموش شده جای افرادیه که در دنیای خودشون مرتکب اشتباهات زیادی شدن و تبعید شدن به دنیای فراموش شده.5296785692150497491\n\n'
    'برای اینکه بتونید از دنیای فراموش شده فرار کنید مجموعه ای از ماموریت ها و دشمن های مختلفی رو باید پشت سر بزارید.5453991094435997597\n\n'
    'باید در طول انجام ماموریت و مبارزه حواستون باشه که نیازمند هستید به منابع مختلف،\n'
    'مثل سکه، الماس و ...5213094908608392768\n\n'
    '5395695537687123235 در طول مبارزات به شما مقدار قابل توجهی منابع تعلق میگیره ولی همیشه به این معنا نیست که قراره کافی باشن پس بهتره به بخش ماموریت ها هم سر بزنید5395695537687123235\n\n'
    'اولین دشمن شما دراخور هستش برای کشتن اون نیاز به\n\n'
    ' 45،000 سکه دارید 5282996373229167849\n\n'
    'و 1750 XP خون لازم دارید🩸\n\n'
    'دراخور دشمن ساده ای نیست پس حواستو جمع کن تو دامش نیوفتی5440660757194744323'
)

BATTLE_INTRO_TEXT = parse_emojis(
    '5395695537687123235<b>توجه</b>5395695537687123235                                            5395695537687123235<b>توجه</b>5395695537687123235\n'
    'مبارز، تو در آستانه ورود به اولین دروازه نبرد هستی!\n'
    'حریف اولت دراخور هستش 6021493696011180326 هیولای بی‌رحمی که از تاریک‌ترین نقاط دنیای وِراث به تاتاروس تبعید شده. 6021562582991640411\n\n'
    'بر اساس قوانین چرخه روزگار، دراخور ۱۵,۰۰۰ HP جان دارد. برای شکست دادن اون با سلاح فعلی‌ات (چاقو)، نیاز به حداقل ۱۰۰ حمله دقیق و ۵۰۰ دقیقه مبارزه خالص زمان هستش! 5917787905308234080\n\n'
    'در این نبرد پینگ‌پونگی، به ازای هر ضربه‌ای که به دراخور میزنی، او هم به تو آسیب می‌رساند! پس برای زنده ماندن به سکه (برای خرید مداوم HP) و برای پیشرفت به XP بالا لازم دارید. 5780382873487939194\n\n'
    'اگر مقدار سکه و HP شما کافی نباشه و وسط میدان کم بیاورید، توی مبارزه به طرز فجیعی شکست میخورید. 5780609587631627157\n\n'
    'پس توی تسک‌ها و با دعوت دوستانت به بازی، مقدار سکه و XP خودت رو به سرعت افزایش بده تا بتوانی در نبرد دوام بیاوری. 6032699501909644905\n\n'
    'و با طلای به دست اومده، سلاح خودت رو ارتقا بده و حیوان نبرد (پِت) بخر تا تایم حملاتت رو کمتر کنی و برای مبارزه های وحشتناک بعدی اماده باشی! 6021608144004716962'
)

# ⚔️ تابع تولید میدان نبرد متحرک (گاد و خفن)
async def get_battle_arena_text(user_id: int, log_msg: str = None):
    boss_hp = int(await get_setting(f"user_{user_id}_boss_hp", 15000))
    boss_max = 15000
    player_hp = int(await get_setting(f"user_{user_id}_hp", 80))
    player_max = 100
    player_shield = int(await get_setting(f"user_{user_id}_shield", 20))
    shield_max = 50
    player_xp = int(await get_setting(f"user_{user_id}_xp", 150))
    xp_max = 500
    coins = int(await get_setting(f"user_{user_id}_coins", 12500))
    gold = int(await get_setting(f"user_{user_id}_gold", 1))

    char_id = await get_setting(f"user_{user_id}_char", "1")
    char_name_raw = await get_setting(f"char{char_id}_name", "زولو")
    char_name = re.sub(r'\d{15,22}', '', char_name_raw).strip()
    char_emoji = await get_setting(f"char{char_id}_emoji", "5958487981772773271")
    if not char_emoji: char_emoji = "5958487981772773271"

    EMOJI_RED_LINE = "5868376419691663420"
    EMOJI_BLACK_LINE = "5870807534389957123"
    EMOJI_BLUE_LINE = "5868656266875769200"
    EMOJI_ORANGE_LINE = "5868587719197724849"
    EMOJI_GREEN_LINE = "5868727352879485936"

    boss_bar = get_progress_bar(boss_hp, boss_max, 5, EMOJI_ORANGE_LINE, EMOJI_BLACK_LINE)
    hp_bar = get_progress_bar(player_hp, player_max, 5, EMOJI_RED_LINE, EMOJI_BLACK_LINE)
    shield_bar = get_progress_bar(player_shield, shield_max, 5, EMOJI_BLUE_LINE, EMOJI_BLACK_LINE)
    xp_bar = get_progress_bar(player_xp, xp_max, 5, EMOJI_GREEN_LINE, EMOJI_BLACK_LINE)

    if not log_msg:
        START_EMOJIS = ["6044381950393719705", "6037533659399985698", "6037163978679916501"]
        log_msg = f"{e(random.choice(START_EMOJIS))} <i>ﺩﺭﺍﺧﻮﺭ ﺑﺎ ﭼﺸﻤﺎﻧﯽ ﺧﻮﻧﯿﻦ ﺑﻪ ﺗﻮ ﺧﯿﺮﻩ ﺷﺪﻩ ﺍﺳﺖ...</i>"

    # براکت‌های زاویه‌دار حذف و جایگزین با کروشه شدند تا ارور HTML نگیریم
    text = (
        f"{e('6021608144004716962')} <b>[ ﻣﯿﺪﺍﻥ ﻧﺒﺮﺩ : ﺗﺎﺗﺎﺭﻭﺱ ]</b> {e('6021608144004716962')}\n\n"
        f"{e('6044381950393719705')} <b>[ ﺩﺷﻤﻦ : ﺩﺭﺍﺧﻮﺭ ]</b>\n"
        f"{e('6037533659399985698')} HP: {boss_bar} <code>[{boss_hp//1000}K / {boss_max//1000}K]</code>\n"
        f"{e('6037163978679916501')} DMG: <code>100 - 300</code>\n\n"
        f"{e(char_emoji)} <b>[ ﺷﻤﺎ : {char_name} ]</b>\n"
        f"{e('6034966544562265361')} HP: {hp_bar} <code>[{player_hp} / {player_max}]</code>\n"
        f"{e('6028551194861899805')} SHD: {shield_bar} <code>[{player_shield} / {shield_max}]</code>\n"
        f"{e('6039679437945968043')} XP: {xp_bar} <code>[{player_xp} / {xp_max}]</code>\n\n"
        f"{e('5958322028531423656')} ﺳﻼﺡ: <code>ﭼﺎﻗﻮ (L1)</code> | {e('5958808923203967006')} ﺁﺳﯿﺐ: <code>150</code>\n"
        f"{e('6032699501909644905')} ﺳﮑﻪ: <code>{coins:,}</code> | {e('5870839969982976188')} ﻃﻼ: <code>{gold}</code>\n\n"
        f"{e('6028251384669805758')} <b>ﮔﺰﺍﺭﺵ ﺯﻧﺪﻩ ﻧﺒﺮﺩ :</b>\n"
        f"{log_msg}"
    )
    return text

UPGRADE_TEXT = parse_emojis("به بخش ارتقا سلاح ها خوش امدید 6021530065794244533\n\nسلاح شما : چاقو (دیفالت بازی) هستش 5830442181906667908\n\nبرای ارتقا روی دکمه چاقو کلیک کنید 5019617635629794161\n\nو برای خرید سلاح جدید روی سلاح مورد نظر کلیک نمایید 5019759554234156094")
WEAPONS = {"چاقو": "knife", "شمشیر": "sword", "کُلت": "colt", "کلاش": "ak47"}

def get_daily_reward_text():
    coins = random.randint(10, 3000)
    xp = random.randint(1, 50)
    return parse_emojis(
        '5785281906459283269 هدیه روزانه\n\n'
        '6034853518202903906 هدیه روزانه آماده است!\n\n'
        f'6032699501909644905 {coins:,} سکه!\n\n'
        f'6035017564478773073 {xp} XP\n\n'
        '5019759554234156094 برای گرفتنش دکمه دریافت جوایز رو بزنید! 5019759554234156094'
    )

# ==========================================
# 📡 ارتباط خام با تلگرام
# ==========================================
async def send_raw_api(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get("ok"): logging.error(f"Telegram API Error [{method}]: {result}")
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
    
    b.button(text=f"پیش‌نبرد {ic(await get_setting('photo_gamestart'))}", callback_data="adm_req_photo_gamestart")
    
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
    b.adjust(2, 2, 2, 2, 2, 2, 2, 1, 1)
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
# 🧩 ساختار کیبوردها
# ==========================================
async def get_raw_main_keyboard(user_id: int):
    return [
        [await btn("حساب کاربری", f"btn_profile_{user_id}", "حساب کاربری", "5987865893084861885"),
         await btn("بازار", f"btn_market_{user_id}", "بازار", "5258024802010026053")],
        [await btn("داستانی", f"btn_story_{user_id}", "داستانی", "5364052602357044385"),
         await btn("مولتی(چند جهانی)", f"btn_multi_{user_id}", "مولتی(چند جهانی)", "5361741454685256344")],
        [await btn("اسکین", f"btn_skin_{user_id}", "اسکین", "5987973065403797894"),
         await btn("ارتقا", f"btn_upgrade_{user_id}", "ارتقا", "5375338737028841420")],
        [await btn("ماموریت ها", f"btn_missions_{user_id}", "ماموریت ها", "5282996373229167849")],
        [await btn("جنگ ها", f"btn_wars_{user_id}", "جنگ ها", "5453991094435997597"),
         await btn("بازار سیاه", f"btn_blackmarket_{user_id}", "بازار سیاه", "5296387887984580731")],
        [await btn("فروشگاه", f"btn_shop_{user_id}", "فروشگاه", "5406683434124859552"),
         await btn("لیدربرد", f"btn_leaderboard_{user_id}", "لیدربرد", "5415655814079723871")],
        [await btn("کلن", f"btn_clan_{user_id}", "کلن", "5978687277390371946"),
         await btn("اخبار", f"btn_news_{user_id}", "اخبار", "5443038326535759644")],
        [await btn("راهنما", f"btn_help_{user_id}", "راهنما", "5282843764451195532"),
         await btn("بستن منو", f"btn_close_{user_id}", "بستن منو", "5210952531676504517")]
    ]

async def get_raw_story_keyboard(user_id: int):
    return [
        [await btn("ادامه بازی", f"btn_continue_{user_id}", "ادامه بازی", "5206607081334906820"),
         await btn("بازگشت", f"btn_backmain_{user_id}", "بازگشت", "5210952531676504517")]
    ]

async def get_raw_gamemenu_keyboard(user_id: int):
    return [
        [await btn("شروع", f"btn_gamestart_{user_id}", "شروع", "6021608144004716962"),
         await btn("ادامه", f"btn_gamecontinue_{user_id}", "ادامه", "6037142916160297263")],
        [await btn("ارتقا", f"btn_gameupg_{user_id}", "ارتقا", "6043954888910576445"),
         await btn("تسک", f"btn_gametask_{user_id}", "تسک", "5780382873487939194")],
        [await btn("جوایز روزانه", f"btn_gamedaily_{user_id}", "جوایز روزانه", "6034834521562553211"),
         await btn("حیوانات نبرد", f"btn_gamepets_{user_id}", "حیوانات نبرد", "6042051380879822629")],
        [await btn("راهنما", f"btn_guide_1_{user_id}", "راهنمای داستانی", "6039577350868310365"),
         await btn("بستن", f"btn_close_{user_id}", "بستن", "6032606743500951856")]
    ]

async def get_raw_battle_intro_keyboard(user_id: int):
    return [
        [await btn("بریم تو دل مبارزه", f"btn_battle_{user_id}", "بریم تو دل مبارزه", "6034966544562265361")],
        [await btn("بازگشت", f"btn_backgamemenu_{user_id}", "بازگشت", "6041794945562451034")]
    ]

async def get_raw_battle_arena_keyboard(user_id: int):
    return [
        [await btn("حمله", f"btn_action_damage_{user_id}", "دمیج دادن", "5958322028531423656"),
         await btn("حمله حیوان", f"btn_action_petdmg_{user_id}", "دمیج حیوان", "6042051380879822629")],
        [await btn("قدرت نمایی", f"btn_action_power_{user_id}", "قدرت", "6037163978679916501"),
         await btn("خرید شیلد", f"btn_action_shield_{user_id}", "خرید شیلد", "6028551194861899805")],
        [await btn("خرید HP", f"btn_action_buyhp_{user_id}", "خرید HP", "6032699501909644905")],
        [await btn("بازگشت به منو داستانی", f"btn_backgamemenu_{user_id}", "بازگشت", "6041794945562451034")]
    ]

async def get_raw_upgrade_keyboard(user_id: int):
    return [
        [await btn("چاقو", f"btn_showweapon_knife_{user_id}", "چاقو", "5830442181906667908")],
        [await btn("شمشیر", f"btn_showweapon_sword_{user_id}", "شمشیر", "5785098292312415025")],
        [await btn("کُلت", f"btn_showweapon_colt_{user_id}", "کُلت", "6034845503793928402")],
        [await btn("کلاش", f"btn_showweapon_ak47_{user_id}", "کلاش", "5181902025721381896")],
        [await btn("تعویض سلاح", f"btn_changeweapon_{user_id}", "تعویض سلاح", "5361741454685256344")],
        [await btn("بازگشت", f"btn_backgamemenu_{user_id}", "بازگشت", "5785177332595561481")]
    ]

async def get_raw_character_keyboard(user_id: int):
    chars = []
    for i in range(1, 5):
        name = await get_setting(f"char{i}_name", f"کاراکتر {i}")
        clean_name = re.sub(r'\d{15,22}', '', name).strip()
        b = await btn(clean_name, f"btn_selectchar_{i}_{user_id}", f"char{i}_emoji", "")
        chars.append(b)
    return [
        [chars[0], chars[1]],
        [chars[2], chars[3]],
        [await btn("بازگشت", f"btn_story_{user_id}", "بازگشت", "5210952531676504517")]
    ]

# ==========================================
# 🚀 تریگرهای دستوری
# ==========================================
@dp.message(F.text == "تاتاروس")
async def trigger_tatarus_menu(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        user_id = message.from_user.id
        photo = await get_setting("photo_main")
        kb = await get_raw_main_keyboard(user_id)
        
        payload = {"chat_id": message.chat.id, "parse_mode": "HTML", "reply_parameters": {"message_id": message.message_id}, "reply_markup": {"inline_keyboard": kb}}
        if photo:
            payload["photo"] = photo
            payload["caption"] = MAIN_TEXT
            await send_raw_api("sendPhoto", payload)
        else:
            payload["text"] = MAIN_TEXT
            await send_raw_api("sendMessage", payload)

@dp.message(F.text.contains("میدان نبرد"))
async def trigger_battle_arena_cmd(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        user_id = message.from_user.id
        try:
            text = await get_battle_arena_text(user_id)
            kb = await get_raw_battle_arena_keyboard(user_id)
            payload = {"chat_id": message.chat.id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": kb}}
            await send_raw_api("sendMessage", payload)
        except Exception as e:
            await send_raw_api("sendMessage", {"chat_id": message.chat.id, "text": f"خطای ربات: {e}"})

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
# 🎛 هندلرهای دکمه‌های شیشه‌ای کاربری
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
        kb = await get_raw_battle_intro_keyboard(owner_id)
        await transition_menu(callback, "photo_gamestart", BATTLE_INTRO_TEXT, kb)
        return await callback.answer()

    elif action == "battle":
        try:
            text = await get_battle_arena_text(owner_id)
            kb = await get_raw_battle_arena_keyboard(owner_id)
            
            has_media = True if (callback.message.photo or callback.message.animation or callback.message.video or callback.message.document) else False
            
            payload = {
                "chat_id": callback.message.chat.id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": kb}
            }

            if has_media:
                await callback.message.delete()
                if callback.message.reply_to_message:
                    payload["reply_parameters"] = {"message_id": callback.message.reply_to_message.message_id}
                result = await send_raw_api("sendMessage", payload)
            else:
                payload["message_id"] = callback.message.message_id
                result = await send_raw_api("editMessageText", payload)
                
            if not result.get("ok"):
                await send_raw_api("sendMessage", {
                    "chat_id": callback.message.chat.id,
                    "text": f"⚠️ ارور تلگرام:\n`{result.get('description')}`",
                    "parse_mode": "Markdown"
                })
                
            return await callback.answer("⚔️ وارد میدان شدی! حواست به جانت باشه...")
            
        except Exception as e:
            logging.error(f"Battle Load Error: {e}")
            return await callback.answer("⚠️ خطای کدنویسی رخ داد!", show_alert=True)

    # 🔴🔥 سیستم قدرتمند چرخه روزگار (Battle Logic)
    elif action.startswith("action_"):
        action_type = parts[2]
        
        boss_hp = int(await get_setting(f"user_{owner_id}_boss_hp", 15000))
        player_hp = int(await get_setting(f"user_{owner_id}_hp", 80))
        shield = int(await get_setting(f"user_{owner_id}_shield", 20))
        coins = int(await get_setting(f"user_{owner_id}_coins", 12500))
        xp = int(await get_setting(f"user_{owner_id}_xp", 150))
        
        log_msg = ""
        if action_type == "damage":
            dmg = random.randint(100, 200)
            boss_hp -= dmg
            boss_dmg = random.randint(10, 30)
            if shield > 0: shield -= boss_dmg
            else: player_hp -= boss_dmg
            log_msg = f"{e(random.choice(ATTACK_EMOJIS))} <i>تو {dmg} دمیج زدی، اما دراخور با {boss_dmg} دمیج به تو حمله کرد!</i>"

        elif action_type == "petdmg":
            char_id = await get_setting(f"user_{owner_id}_char", "1")
            has_pet = await get_setting(f"user_{owner_id}_pet_{char_id}") == "1"
            if not has_pet:
                return await callback.answer("⚠️ شما هنوز برای این کاراکتر حیوان نبرد نخریده‌اید!", show_alert=True)
            dmg = random.randint(300, 500)
            boss_hp -= dmg
            log_msg = f"{e(random.choice(ATTACK_EMOJIS))} <i>حیوان تو به طرز وحشیانه‌ای {dmg} دمیج وارد کرد! دراخور گیج شده!</i>"

        elif action_type == "power":
            dmg = random.randint(200, 400)
            boss_hp -= dmg
            player_hp -= random.randint(20, 50)
            log_msg = f"{e(random.choice(BOSS_EMOJIS))} <i>قدرت نمایی کردی و {dmg} دمیج زدی، اما خودت هم آسیب دیدی!</i>"

        elif action_type == "shield":
            if coins >= 1000 and shield < 50:
                coins -= 1000
                shield = min(50, shield + 20)
                log_msg = f"{e(random.choice(HEAL_EMOJIS))} <i>با ۱۰۰۰ سکه سپر خود را شارژ کردی! دراخور عصبانی است...</i>"
            else:
                return await callback.answer("سکه کافی نیست یا سپرت پر است! (قیمت: ۱۰۰۰ سکه)", show_alert=True)

        elif action_type == "buyhp":
            if coins >= 500 and player_hp < 100:
                coins -= 500
                player_hp = min(100, player_hp + 30)
                log_msg = f"{e(random.choice(HEAL_EMOJIS))} <i>معجون خون خریدی (+۳۰ HP)! دراخور پوزخند می‌زند...</i>"
            else:
                return await callback.answer("سکه کافی نیست یا خونت پر است! (قیمت: ۵۰۰ سکه)", show_alert=True)

        if shield < 0:
            player_hp += shield
            shield = 0
        
        # بررسی زنده ماندن یا مردن
        if player_hp <= 0:
            player_hp = 100
            coins = max(0, coins - 2000)
            await set_setting(f"user_{owner_id}_hp", str(player_hp))
            await set_setting(f"user_{owner_id}_coins", str(coins))
            await callback.answer("💀 تو در میدان کشته شدی و ۲۰۰۰ سکه از دست دادی! دوباره تلاش کن...", show_alert=True)
            kb = await get_raw_gamemenu_keyboard(owner_id)
            await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
            return
            
        if boss_hp <= 0:
            boss_hp = 15000
            coins += 50000
            xp += 200
            await set_setting(f"user_{owner_id}_boss_hp", str(boss_hp))
            await set_setting(f"user_{owner_id}_coins", str(coins))
            await set_setting(f"user_{owner_id}_xp", str(xp))
            await callback.answer("🎉 دراخور را شکست دادی! ۵۰,۰۰۰ سکه و ۲۰۰ XP جایزه گرفتی!", show_alert=True)
            kb = await get_raw_gamemenu_keyboard(owner_id)
            await transition_menu(callback, "photo_gamemenu", GAME_MENU_TEXT, kb)
            return

        await set_setting(f"user_{owner_id}_boss_hp", str(boss_hp))
        await set_setting(f"user_{owner_id}_hp", str(player_hp))
        await set_setting(f"user_{owner_id}_shield", str(shield))
        await set_setting(f"user_{owner_id}_coins", str(coins))
        
        text = await get_battle_arena_text(owner_id, log_msg)
        kb = await get_raw_battle_arena_keyboard(owner_id)
        
        payload = {"chat_id": callback.message.chat.id, "message_id": callback.message.message_id, "text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": kb}}
        await send_raw_api("editMessageText", payload)
        return await callback.answer()

    elif action == "gameupg":
        kb = await get_raw_upgrade_keyboard(owner_id)
        await transition_menu(callback, "photo_upgrade", UPGRADE_TEXT, kb)
        return await callback.answer()

    elif action == "showweapon":
        weapon_type = parts[2]
        weapon_fa = [k for k, v in WEAPONS.items() if v == weapon_type][0]
        weapon_text = parse_emojis(f"بخش اختصاصی سلاح {weapon_fa} (در حال توسعه)")
        kb = [[await btn("بازگشت", f"btn_backupgrade_{owner_id}", "بازگشت", "5785177332595561481")]]
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
            [await btn("دریافت جوایز روزانه", f"btn_claimdaily_{owner_id}", "دریافت جوایز روزانه", "6028565819225542441")],
            [await btn("بازگشت", f"btn_backgamemenu_{owner_id}", "بازگشت", "6032606743500951856")]
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
        
        if is_purchased: pet_text += '\n\nخریداری شده <tg-emoji emoji-id="6028565819225542441">✨</tg-emoji>'
        else: pet_text += '\n\nخریداری نشده <tg-emoji emoji-id="6032606743500951856">✨</tg-emoji>'

        kb = []
        if is_purchased: 
            kb.append([await btn("فعال کردن برای نبرد", f"btn_activatepet_{char_id}_{owner_id}", "فعال کردن برای نبرد", "5780857858216173092")])
        else: 
            emoji_id = await get_emoji("خریدن حیوان", "6028565819225542441")
            kb.append([{"text": "خریدن حیوان", "url": f"https://t.me/{BOT_USERNAME}?start=buypet_{char_id}", "icon_custom_emoji_id": str(emoji_id)}])
            
        kb.append([await btn("بازگشت", f"btn_backgamemenu_{owner_id}", "بازگشت", "6032606743500951856")])
        
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
        if page > 1: nav_btns.append(await btn("قبلی", f"btn_guide_{page-1}_{owner_id}", "قبلی", "5210952531676504517"))
        if page < total_pages: nav_btns.append(await btn("بعدی", f"btn_guide_{page+1}_{owner_id}", "بعدی", "5210952531676504517"))
        
        kb = []
        if nav_btns: kb.append(nav_btns)
        kb.append([await btn("بازگشت", f"btn_backgamemenu_{owner_id}", "بازگشت", "6032606743500951856")])
        
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
    print(f"🤖 ربات تاتاروس ({BOT_USERNAME}) با دیتابیس عظیم ایموجی‌ها و چرخه روزگار فعال شد!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
