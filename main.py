import os
import sys
import logging
import asyncio
import re
import html
import sqlite3
from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import jdatetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ryno_sender_bot")

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "").strip()

try:
    PENDING_PAYMENT_TTL_MINUTES = int(os.getenv("PENDING_PAYMENT_TTL_MINUTES", "15").strip() or "15")
except Exception:
    PENDING_PAYMENT_TTL_MINUTES = 15

TZ_NAME = os.getenv("TZ_NAME", "Asia/Tehran").strip() or "Asia/Tehran"
try:
    TZ = ZoneInfo(TZ_NAME)
except Exception:
    TZ = ZoneInfo("UTC")

def _parse_daily_limit(raw: str) -> int:
    s = (str(raw) or "").strip()
    if not s: return 3000
    mult = 1
    if s.lower().endswith("k"):
        mult = 1000
        s = s[:-1].strip()
    try: v = int(s)
    except: return 3000
    if mult == 1 and 1 <= v <= 50: return v * 1000
    return max(0, v * mult)

OWNER_CHAT_ID_RAW = os.getenv("OWNER_CHAT_ID", "").strip()
OWNER_CHAT_ID = int(OWNER_CHAT_ID_RAW) if OWNER_CHAT_ID_RAW.isdigit() else None

SECOND_OWNER_ID_RAW = os.getenv("SECOND_OWNER_ID", "").strip()
SECOND_OWNER_ID = int(SECOND_OWNER_ID_RAW) if SECOND_OWNER_ID_RAW.isdigit() else None

BOT_ADMIN_IDS_RAW = os.getenv("BOT_ADMIN_IDS", "").strip()
BOT_ADMIN_IDS: set[int] = set()
if BOT_ADMIN_IDS_RAW:
    for part in BOT_ADMIN_IDS_RAW.split(","):
        p = part.strip()
        if p.isdigit(): BOT_ADMIN_IDS.add(int(p))

if OWNER_CHAT_ID is not None:
    BOT_ADMIN_IDS.add(OWNER_CHAT_ID)
if SECOND_OWNER_ID is not None:
    BOT_ADMIN_IDS.add(SECOND_OWNER_ID)

BROADCAST_SLEEP_SECONDS = float(os.getenv("BROADCAST_SLEEP_SECONDS", "0.07").strip() or "0.07")

# Default Texts
DEFAULT_WELCOME_TEXT = (
    "به ربات رسمی «راینو شاپ / راینو سندر» خوش اومدی! 🚀\n"
    "اینجا تبلیغات تلگرام رو حرفه‌ای، سریع و هدفمند انجام می‌دیم.\n\n"
    "ما یک تیم تخصصی خدمات مجازی هستیم با:\n"
    "🥇 بیش از ۲ سال سابقه حرفه‌ای در تبلیغات تلگرام\n"
    "🌟 بیش از ۵ سال تجربه در ارائه خدمات مجازی\n\n"
    "👇 برای شروع از منوی اصلی یکی از گزینه‌ها رو انتخاب کن."
)
DEFAULT_CARD_TEXT = (
    "💳 [ 6219861845420602 ]\n"
    "👤 به نام : نامق احمدی\n\n"
    "📸 لطفاً واریز رو انجام بده و بعد روی دکمه «واریز کردم ✅» کلیک کن تا فیش رو برامون بفرستی."
)
DEFAULT_RATES_TEXT = (
    "لیست قیمت پکیج‌ها:\n\n"
    "🔹 200 پخشی = 150,000 تومان\n"
    "🔹 300 پخشی = 240,000 تومان\n"
    "🔹 400 پخشی = 330,000 تومان\n"
    "🔹 500 پخشی = 430,000 تومان\n"
    "🔹 600 پخشی = 500,000 تومان\n"
    "🔹 800 پخشی = 600,000 تومان\n"
    "🔹 1000 پخشی = 650,000 تومان"
)

# Callbacks and State Keys
CB_SLOT_PREFIX = "slot|"
CB_PACKAGE_PREFIX = "pkg|"
CB_VERIF_PREFIX = "verif|"
CB_DISCOUNT_PREFIX = "discount|"
CB_PAYMENT_PREFIX = "pay|"
CB_DEST_PREFIX = "dest|"
CB_ADMIN_USERS_PREFIX = "adminusers|"
CB_TAKHFIF_PKG_PREFIX = "takhpkg|"

UD_STATE = "user_state"
STATE_BROADCAST = "state_broadcast"
STATE_WALLET_AMOUNT = "state_wallet_amt"
STATE_WALLET_RECEIPT = "state_wallet_receipt"
STATE_PAY_COUPON = "state_pay_coupon"
STATE_PAY_RECEIPT = "state_pay_receipt"
STATE_VERIF_PHOTO = "state_verif_photo"
STATE_VERIF_CARD = "state_verif_card"
STATE_DEST_LINKS = "state_dest_links"
STATE_DEST_DESC = "state_dest_desc"
STATE_ADMIN_CANCEL_DAY = "state_admin_cancel_day"
STATE_ADMIN_CANCEL_TIME = "state_admin_cancel_time"
STATE_EDIT_WELCOME = "state_edit_welcome"
STATE_EDIT_CARD = "state_edit_card"
STATE_EDIT_RATES = "state_edit_rates"
STATE_EDIT_PKG_PRICE = "state_edit_pkg_price"
STATE_EDIT_DAILY_LIMIT = "state_edit_daily_limit"
STATE_TAKHFIF_CODE = "state_takhfif_code"
STATE_TAKHFIF_USES = "state_takhfif_uses"
STATE_TAKHFIF_DUR = "state_takhfif_dur"
STATE_TAKHFIF_AMT = "state_takhfif_amt"
STATE_TAKHFIF_PKG = "state_takhfif_pkg"

UD_PENDING_SLOT_ISO = "pending_slot_iso"
UD_PAYMENT_RESERVATION_ID = "payment_reservation_id"
UD_DEST_RESERVATION_ID = "dest_reservation_id"
UD_DEST_LINKS_LIST = "dest_links_list"
UD_VERIFICATION_REQUEST_ID = "verification_request_id"
BOTDATA_USER_AWAIT_BANNER = "user_await_banner"
BOTDATA_OWNER_PENDING_REJECT = "owner_pending_payment_reject"

DEST_FINISH_TEXT = "پایان"

DAY_SAT = "شنبه"
DAY_SUN = "یکشنبه"
DAY_MON = "دوشنبه"
DAY_TUE = "سه شنبه"
DAY_WED = "چهارشنبه"
DAY_THU = "پنجشنبه"
DAY_FRI = "جمعه"

DAY_TO_PERSIAN_WEEKDAY = {
    DAY_SAT: 0, DAY_SUN: 1, DAY_MON: 2, DAY_TUE: 3, DAY_WED: 4, DAY_THU: 5, DAY_FRI: 6,
}

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_TO_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

REMINDER_MINUTES_BEFORE = int(os.getenv("REMINDER_MINUTES_BEFORE", "15").strip() or "15")
REMINDER_INTERVAL_SECONDS = int(os.getenv("REMINDER_INTERVAL_SECONDS", "30").strip() or "30")
REMINDER_WINDOW_SECONDS = int(os.getenv("REMINDER_WINDOW_SECONDS", "90").strip() or "90")

_REMINDER_GROUP_RAW = os.getenv("REMINDER_GROUP_CHAT_ID", "-1003586523851").strip()
try:
    REMINDER_GROUP_CHAT_ID: int | None = int(_REMINDER_GROUP_RAW) if _REMINDER_GROUP_RAW else None
except Exception:
    REMINDER_GROUP_CHAT_ID = None

# ==========================================
# DATABASE LAYER
# ==========================================
DEFAULT_DB_PATH = "db.sqlite3"

def _db_path() -> str:
    railway_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
    explicit = os.getenv("DB_PATH", "").strip()
    if explicit:
        if railway_mount and not os.path.isabs(explicit):
            return os.path.join(railway_mount, explicit)
        return explicit
    if railway_mount:
        return os.path.join(railway_mount, DEFAULT_DB_PATH)
    return DEFAULT_DB_PATH

def init_db() -> None:
    db_path = _db_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                username TEXT,
                is_subscribed INTEGER NOT NULL DEFAULT 0,
                subscribed_at TEXT,
                unsubscribed_at TEXT,
                wallet_balance INTEGER NOT NULL DEFAULT 0,
                referrer_id INTEGER
            );
        """)
        cols = {row[1] for row in con.execute("PRAGMA table_info(users)").fetchall()}
        if "wallet_balance" not in cols: con.execute("ALTER TABLE users ADD COLUMN wallet_balance INTEGER NOT NULL DEFAULT 0")
        if "referrer_id" not in cols: con.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER")
        
        con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);")
        
        con.execute("CREATE TABLE IF NOT EXISTS packages (count INTEGER PRIMARY KEY, price INTEGER, is_active INTEGER DEFAULT 1);")
        pkg_cnt = con.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
        if pkg_cnt == 0:
            defaults = [(200,150000),(300,240000),(400,330000),(500,430000),(600,500000),(800,600000),(1000,650000)]
            con.executemany("INSERT INTO packages(count, price) VALUES (?, ?)", defaults)
            
        con.execute("""
            CREATE TABLE IF NOT EXISTS wallet_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                photo_file_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reserved_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'booked',
                package_count INTEGER,
                group_link TEXT,
                promo_photo_file_id TEXT,
                reminder_sent_at TEXT,
                username TEXT,
                destination_links TEXT
            );
        """)
        r_cols = {row[1] for row in con.execute("PRAGMA table_info(reservations)").fetchall()}
        if "group_link" not in r_cols: con.execute("ALTER TABLE reservations ADD COLUMN group_link TEXT")
        if "package_count" not in r_cols: con.execute("ALTER TABLE reservations ADD COLUMN package_count INTEGER")
        if "promo_photo_file_id" not in r_cols: con.execute("ALTER TABLE reservations ADD COLUMN promo_photo_file_id TEXT")
        if "destination_links" not in r_cols: con.execute("ALTER TABLE reservations ADD COLUMN destination_links TEXT")

        con.execute("DROP INDEX IF EXISTS ux_reservations_reserved_at_active;")
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_reservations_reserved_at_booked ON reservations(reserved_at) WHERE status = 'booked';")
        
        con.execute("""
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                card_number TEXT,
                coupon_code TEXT,
                coupon_percent INTEGER,
                coupon_amount_toman INTEGER,
                package_count INTEGER,
                receipt_photo_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewer_id INTEGER,
                reject_reason TEXT,
                is_wallet INTEGER DEFAULT 0
            );
        """)
        p_cols = {row[1] for row in con.execute("PRAGMA table_info(payment_requests)").fetchall()}
        if "is_wallet" not in p_cols: con.execute("ALTER TABLE payment_requests ADD COLUMN is_wallet INTEGER DEFAULT 0")

        con.execute("""
            CREATE TABLE IF NOT EXISTS discount_codes (
                code TEXT PRIMARY KEY, percent INTEGER NOT NULL, amount_toman INTEGER, max_uses INTEGER NOT NULL,
                used_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, created_by INTEGER NOT NULL,
                expires_at TEXT NOT NULL, package_count INTEGER, is_active INTEGER NOT NULL DEFAULT 1
            );
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS verification_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, username TEXT, card_number TEXT NOT NULL,
                photo_file_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
                reviewed_at TEXT, reviewer_id INTEGER, decision_reason TEXT
            );
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS verified_cards (
                user_id INTEGER PRIMARY KEY, username TEXT, card_number TEXT NOT NULL,
                verified_at TEXT NOT NULL, verifier_id INTEGER
            );
        """)

# DB Helpers
def get_setting(key: str, default_val: str) -> str:
    with sqlite3.connect(_db_path()) as con:
        row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default_val

def set_setting(key: str, value: str):
    with sqlite3.connect(_db_path()) as con:
        con.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

def get_daily_limit() -> int:
    return _parse_daily_limit(get_setting("daily_limit", os.getenv("DAILY_LIMIT", "3000")))

def get_packages() -> list:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT count, price, is_active FROM packages ORDER BY count ASC").fetchall()

def get_active_packages() -> list:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT count, price FROM packages WHERE is_active=1 ORDER BY count ASC").fetchall()

def update_package(count: int, price: int=None, toggle: bool=False):
    with sqlite3.connect(_db_path()) as con:
        if toggle:
            con.execute("UPDATE packages SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE count=?", (count,))
        if price is not None:
            con.execute("UPDATE packages SET price = ? WHERE count=?", (price, count))

def get_package_price(count: int) -> int:
    with sqlite3.connect(_db_path()) as con:
        row = con.execute("SELECT price FROM packages WHERE count=?", (count,)).fetchone()
        return row[0] if row else 0

def upsert_user(user_id: int, username: str | None, referrer_id: int | None = None) -> bool:
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        row = con.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        is_new = row is None
        if is_new:
            con.execute("INSERT INTO users(user_id, first_seen_at, last_seen_at, username, referrer_id) VALUES (?, ?, ?, ?, ?)",
                        (user_id, now_iso, now_iso, username, referrer_id))
        else:
            con.execute("UPDATE users SET last_seen_at=?, username=COALESCE(?, username) WHERE user_id=?", (now_iso, username, user_id))
        return is_new

def get_wallet_balance(user_id: int) -> int:
    with sqlite3.connect(_db_path()) as con:
        row = con.execute("SELECT wallet_balance FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else 0

def add_wallet_balance(user_id: int, amount: int):
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id=?", (amount, user_id))

def get_referrals(user_id: int) -> list:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT user_id, username FROM users WHERE referrer_id=?", (user_id,)).fetchall()

def create_wallet_req(user_id: int, amount: int, photo: str) -> int:
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        return con.execute("INSERT INTO wallet_requests(user_id, amount, photo_file_id, created_at) VALUES (?, ?, ?, ?)",
                           (user_id, amount, photo, now_iso)).lastrowid

def update_wallet_req(req_id: int, status: str):
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE wallet_requests SET status=? WHERE id=?", (status, req_id))

def get_wallet_req(req_id: int) -> tuple:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT user_id, amount, status FROM wallet_requests WHERE id=?", (req_id,)).fetchone()

def process_referral_reward(user_id: int, purchase_amount: int, bot):
    with sqlite3.connect(_db_path()) as con:
        ref = con.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,)).fetchone()
    if ref and ref[0]:
        reward = int(purchase_amount * 0.05)
        if reward > 0:
            add_wallet_balance(ref[0], reward)
            asyncio.create_task(
                bot.send_message(
                    chat_id=ref[0],
                    text=f"🎉 تبریک! کاربر زیرمجموعه شما خریدی انجام داد و مبلغ {_format_toman(reward)} (۵ درصد پورسانت) به کیف پول شما واریز شد 💰"
                )
            )

def get_admin_stats_detailed() -> tuple:
    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    since_24h = (now_utc - timedelta(hours=24)).isoformat(timespec="seconds")
    since_7d = (now_utc - timedelta(days=7)).isoformat(timespec="seconds")
    since_30d = (now_utc - timedelta(days=30)).isoformat(timespec="seconds")
    
    with sqlite3.connect(_db_path()) as con:
        tu = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        a24 = con.execute("SELECT COUNT(*) FROM users WHERE last_seen_at >= ?", (since_24h,)).fetchone()[0]
        a7d = con.execute("SELECT COUNT(*) FROM users WHERE last_seen_at >= ?", (since_7d,)).fetchone()[0]
        a30 = con.execute("SELECT COUNT(*) FROM users WHERE last_seen_at >= ?", (since_30d,)).fetchone()[0]
        rb = con.execute("SELECT COUNT(*) FROM reservations WHERE status='booked'").fetchone()[0]
        pa = con.execute("SELECT COUNT(*) FROM payment_requests WHERE status='approved'").fetchone()[0]
        va = con.execute("SELECT COUNT(*) FROM verification_requests WHERE status='approved'").fetchone()[0]
    return tu, a24, a7d, a30, rb, pa, va

def is_slot_reserved(reserved_at: datetime) -> bool:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT 1 FROM reservations WHERE reserved_at=? AND status='booked'", (reserved_at.isoformat(timespec="seconds"),)).fetchone() is not None

def sum_booked_pakhsh(date_iso: str) -> int:
    with sqlite3.connect(_db_path()) as con:
        r = con.execute("SELECT SUM(COALESCE(package_count,1)) FROM reservations WHERE status='booked' AND substr(reserved_at,1,10)=?", (date_iso,)).fetchone()
        return int(r[0] or 0)

def release_stale_reservations():
    thr = (datetime.utcnow() - timedelta(minutes=PENDING_PAYMENT_TTL_MINUTES)).isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE reservations SET status='cancelled' WHERE status='pending_payment' AND created_at <= ? AND NOT EXISTS(SELECT 1 FROM payment_requests WHERE reservation_id=reservations.id)", (thr,))

def get_verified_card_number(user_id: int):
    with sqlite3.connect(_db_path()) as con:
        r = con.execute("SELECT card_number FROM verified_cards WHERE user_id=?", (user_id,)).fetchone()
        return r[0] if r else None

def create_verification_request(user_id: int, username: str | None, card_number: str, photo_file_id: str) -> int:
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        return con.execute("INSERT INTO verification_requests(user_id, username, card_number, photo_file_id, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
                           (user_id, username, card_number, photo_file_id, now_iso)).lastrowid

def get_verification_request(req_id: int) -> tuple:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT user_id, username, card_number, status FROM verification_requests WHERE id=?", (req_id,)).fetchone()

def set_verification_status(req_id: int, status: str, reviewer_id: int | None, reason: str | None = None):
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE verification_requests SET status=?, reviewed_at=?, reviewer_id=?, decision_reason=? WHERE id=?", (status, now_iso, reviewer_id, reason, req_id))

def upsert_verified_card(user_id: int, username: str | None, card_number: str, verifier_id: int | None):
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        con.execute("""INSERT INTO verified_cards(user_id, username, card_number, verified_at, verifier_id) VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, card_number=excluded.card_number, verified_at=excluded.verified_at, verifier_id=excluded.verifier_id""",
                    (user_id, username, card_number, now_iso, verifier_id))

def normalize_discount_code(code: str) -> str:
    return code.strip().lower()

def create_discount_code(code: str, percent: int, amount_toman: int | None, max_uses: int, expires_at_iso: str, package_count: int | None, created_by: int):
    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    norm = normalize_discount_code(code)
    with sqlite3.connect(_db_path()) as con:
        con.execute("INSERT INTO discount_codes(code, percent, amount_toman, max_uses, used_count, created_at, created_by, expires_at, package_count, is_active) VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 1)",
                    (norm, int(percent), amount_toman, int(max_uses), now_iso, int(created_by), expires_at_iso, package_count))

def consume_discount_code(code: str, now_iso: str) -> bool:
    norm = normalize_discount_code(code)
    with sqlite3.connect(_db_path()) as con:
        cur = con.execute("UPDATE discount_codes SET used_count = used_count + 1 WHERE code=? AND is_active=1 AND used_count < max_uses AND expires_at > ?", (norm, now_iso))
        return cur.rowcount == 1

def can_use_discount_code(code: str, now_iso: str, package_count: int | None) -> tuple:
    with sqlite3.connect(_db_path()) as con:
        dc = con.execute("SELECT code, percent, amount_toman, max_uses, used_count, expires_at, package_count, is_active FROM discount_codes WHERE code=?", (normalize_discount_code(code),)).fetchone()
    if not dc: return False, "not_found", None, None, None
    if int(dc[7]) != 1: return False, "inactive", None, None, None
    req_pkg = int(dc[6]) if dc[6] is not None else None
    if req_pkg is not None and (package_count is None or int(package_count) != req_pkg):
        return False, "wrong_package", None, None, req_pkg
    try:
        if datetime.fromisoformat(now_iso) >= datetime.fromisoformat(dc[5]): return False, "expired", None, None, req_pkg
    except: return False, "expired", None, None, req_pkg
    if int(dc[4]) >= int(dc[3]): return False, "used_up", None, None, req_pkg
    amt = int(dc[2]) if dc[2] is not None else None
    pct = int(dc[1]) if dc[1] is not None else 0
    return True, "ok", pct, amt, req_pkg

def create_payment_request(
    reservation_id: int, user_id: int, username: str | None, card_number: str,
    coupon_code: str | None, coupon_percent: int | None, coupon_amount_toman: int | None,
    package_count: int | None, receipt_photo_file_id: str
) -> int:
    created_at = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        cur = con.execute(
            """INSERT INTO payment_requests(
                reservation_id, user_id, username, card_number, coupon_code, coupon_percent, coupon_amount_toman, package_count, receipt_photo_file_id, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (reservation_id, user_id, username, card_number, coupon_code, coupon_percent, coupon_amount_toman, package_count, receipt_photo_file_id, created_at)
        )
        return int(cur.lastrowid)

def get_payment_request(payment_id: int) -> Optional[tuple]:
    with sqlite3.connect(_db_path()) as con:
        return con.execute("SELECT id, reservation_id, user_id, username, card_number, coupon_code, coupon_percent, coupon_amount_toman, package_count, receipt_photo_file_id, status, created_at, reviewed_at, reviewer_id, reject_reason FROM payment_requests WHERE id=?", (payment_id,)).fetchone()

def set_payment_status(payment_id: int, status: str, reviewer_id: int | None, reject_reason: str | None = None):
    reviewed_at = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE payment_requests SET status=?, reviewed_at=?, reviewer_id=?, reject_reason=? WHERE id=?", (status, reviewed_at, reviewer_id, reject_reason, payment_id))

def set_reservation_status(reservation_id: int, status: str):
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE reservations SET status=? WHERE id=?", (status, reservation_id))

def cancel_booked_reservation_by_reserved_at(reserved_at: datetime) -> int:
    reserved_iso = reserved_at.isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        cur = con.execute("UPDATE reservations SET status='cancelled' WHERE reserved_at=? AND status='booked'", (reserved_iso,))
        return int(cur.rowcount or 0)

def try_hold_slot_pending_payment(user_id: int, reserved_at: datetime) -> int | None:
    created_at = datetime.utcnow().isoformat(timespec="seconds")
    reserved_iso = reserved_at.isoformat(timespec="seconds")
    with sqlite3.connect(_db_path()) as con:
        booked = con.execute("SELECT 1 FROM reservations WHERE reserved_at = ? AND status = 'booked' LIMIT 1", (reserved_iso,)).fetchone()
        if booked: return None
        cur = con.execute("INSERT INTO reservations(user_id, reserved_at, created_at, status) VALUES (?, ?, ?, 'pending_payment')", (int(user_id), reserved_iso, created_at))
        return int(cur.lastrowid)

def try_book_reservation(reservation_id: int) -> bool:
    try:
        with sqlite3.connect(_db_path()) as con:
            con.execute("UPDATE reservations SET status = 'booked' WHERE id = ?", (int(reservation_id),))
        return True
    except sqlite3.IntegrityError:
        return False

def update_reservation_promo(reservation_id: int, username: str | None, group_link: str | None, promo_photo_file_id: str | None):
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE reservations SET username=COALESCE(?, username), group_link=COALESCE(?, group_link), promo_photo_file_id=COALESCE(?, promo_photo_file_id) WHERE id=?", (username, group_link, promo_photo_file_id, reservation_id))

def update_reservation_destination_links(reservation_id: int, destination_links: str | None):
    with sqlite3.connect(_db_path()) as con:
        con.execute("UPDATE reservations SET destination_links=? WHERE id=?", (destination_links, reservation_id))

def list_broadcast_user_ids() -> list[int]:
    with sqlite3.connect(_db_path()) as con:
        rows = con.execute("SELECT user_id FROM users WHERE unsubscribed_at IS NULL ORDER BY first_seen_at ASC").fetchall()
    return [int(r[0]) for r in rows]

# ==========================================
# UTILITIES
# ==========================================
def _to_fa_digits(text: str) -> str: return str(text).translate(PERSIAN_DIGITS)
def _format_toman(amount: int) -> str: return f"{_to_fa_digits(f'{int(amount):,}')} تومان"

def _is_admin(user_id: int | None) -> bool:
    if not user_id: return False
    return user_id in BOT_ADMIN_IDS

def _is_member(member) -> bool:
    return member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}

def _parse_toman_amount(text: str) -> int | None:
    t = text.strip().translate(FA_TO_EN_DIGITS).lower()
    t = t.replace(",", " ").replace("_", " ")
    t = re.sub(r"\s+", " ", t)
    t = t.replace("تومان", "").replace("تومن", "").strip()
    mult = 1
    if "میلیون" in t:
        mult = 1_000_000
        t = t.replace("میلیون", "").strip()
    elif "هزار" in t:
        mult = 1_000
        t = t.replace("هزار", "").strip()
    elif t.endswith("k"):
        mult = 1_000
        t = t[:-1].strip()
    m = re.search(r"\d+", t)
    if not m: return None
    try: v = int(m.group(0))
    except: return None
    if v <= 0: return None
    return int(v) * int(mult)

def _parse_duration_to_timedelta(text: str) -> timedelta | None:
    t = text.strip()
    m = re.fullmatch(r"(\d+)\s*(روز|ساعت|دقیقه)", t)
    if not m:
        m = re.fullmatch(r"(\d+)\s*([dhm])", t, flags=re.IGNORECASE)
    if not m: return None
    value = int(m.group(1))
    unit = m.group(2).lower()
    if value <= 0: return None
    if unit in ("روز", "d"): return timedelta(days=value)
    if unit in ("ساعت", "h"): return timedelta(hours=value)
    if unit in ("دقیقه", "m"): return timedelta(minutes=value)
    return None

def _normalize_card_number(text: str) -> str | None:
    compact = re.sub(r"[\s-]", "", text.strip()).translate(FA_TO_EN_DIGITS)
    if not re.fullmatch(r"[0-9]{16}", compact): return None
    return compact

def _normalize_hhmm(text: str) -> str | None:
    raw = (text or "").strip().translate(FA_TO_EN_DIGITS)
    if not re.fullmatch(r"\d{1,2}:\d{2}", raw): return None
    hh_s, mm_s = raw.split(":", 1)
    try:
        hh = int(hh_s)
        mm = int(mm_s)
    except: return None
    if not (0 <= hh <= 23 and 0 <= mm <= 59): return None
    return f"{hh:02d}:{mm:02d}"

def _format_seen_at(seen_at_iso_utc: str | None) -> str:
    if not seen_at_iso_utc: return "نامشخص"
    try:
        dt = datetime.fromisoformat(seen_at_iso_utc)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt = dt.astimezone(TZ)
        jdate = jdatetime.date.fromgregorian(date=dt.date())
        date_str = f"{jdate.year:04d}/{jdate.month:02d}/{jdate.day:02d}".translate(PERSIAN_DIGITS)
        time_str = dt.strftime("%H:%M").translate(PERSIAN_DIGITS)
        return f"{date_str} - {time_str}"
    except: return seen_at_iso_utc

def _next_date_for_persian_weekday(selected_persian_weekday: int, now: datetime) -> datetime.date:
    today_persian = (now.weekday() + 2) % 7
    days_ahead = (selected_persian_weekday - today_persian) % 7
    if days_ahead == 0 and now.timetz() >= time(23, 0, tzinfo=TZ):
        days_ahead = 7
    return (now + timedelta(days=days_ahead)).date()

def _time_slots() -> list[time]:
    return [time(20, 30), time(21, 0), time(21, 30), time(22, 0), time(22, 30), time(23, 0)]

def _apply_discount(amount: int, percent: int | None) -> int:
    p = int(percent or 0)
    if p <= 0: return int(amount)
    if p >= 100: return 0
    return int(amount) * (100 - p) // 100

def _apply_discount_amount(amount: int, percent: int | None, amount_toman: int | None) -> int:
    if amount_toman is not None and int(amount_toman) > 0:
        return max(0, int(amount) - min(int(amount), int(amount_toman)))
    return _apply_discount(int(amount), percent)

# ==========================================
# KEYBOARDS
# ==========================================
def _main_menu_keyboard(user_id: int | None = None) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton("💳 حساب کاربری"), KeyboardButton("⏰ رزرو تایم")],
        [KeyboardButton("👥 زیر مجموعه گیری"), KeyboardButton("📜 نرخ")],
        [KeyboardButton("📞 ارتباط با ادمین"), KeyboardButton("🪪 احراز هویت")]
    ]
    if _is_admin(user_id): kb.append([KeyboardButton("پنل مدیریت 🛠")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def _admin_panel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("📊 آمار"), KeyboardButton("📣 همگانی")],
        [KeyboardButton("🎟️ کد تخفیف"), KeyboardButton("🗑️ حذف رزرو")],
        [KeyboardButton("⚙️ تنظیمات و ویرایش")],
        [KeyboardButton("بازگشت")]
    ], resize_keyboard=True)

def _settings_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 ویرایش خوش امدگویی"), KeyboardButton("💳 ویرایش شماره کارت")],
        [KeyboardButton("📜 ویرایش متن نرخ"), KeyboardButton("📦 ویرایش موجودی ها")],
        [KeyboardButton("📊 ویرایش محدودیت روزانه")],
        [KeyboardButton("🔙 بازگشت به پنل")]
    ], resize_keyboard=True)

def _back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("بازگشت")]], resize_keyboard=True)

def _cancel_broadcast_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("کنسل کردن و بازگشت 🔙")]], resize_keyboard=True)

def _reserve_days_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(DAY_SAT), KeyboardButton(DAY_SUN)],
        [KeyboardButton(DAY_MON), KeyboardButton(DAY_TUE)],
        [KeyboardButton(DAY_WED), KeyboardButton(DAY_THU)],
        [KeyboardButton(DAY_FRI)],
        [KeyboardButton("بازگشت")],
    ], resize_keyboard=True)

def _finish_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(DEST_FINISH_TEXT)], [KeyboardButton("بازگشت")]
    ], resize_keyboard=True)

async def check_membership_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not REQUIRED_CHANNEL: return True
    user = update.effective_user
    if not user: return False
    try:
        if _is_member(await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)): return True
    except: pass
    
    url = CHANNEL_JOIN_URL or f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("عضویت در کانال 📢", url=url)],
        [InlineKeyboardButton("تایید عضویت ✅", callback_data="check_join")]
    ])
    
    if update.message:
        await update.message.reply_text(get_setting("welcome_text", DEFAULT_WELCOME_TEXT), reply_markup=kb)
    return False

# ==========================================
# HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user: return
    
    ref_id = None
    if context.args and context.args[0].startswith("ref_"):
        try: ref_id = int(context.args[0].split("_")[1])
        except: pass

    is_new = await asyncio.to_thread(upsert_user, user.id, f"@{user.username}" if user.username else None, ref_id)
    
    if not await check_membership_gate(update, context): return
    await update.message.reply_text(get_setting("welcome_text", DEFAULT_WELCOME_TEXT), reply_markup=_main_menu_keyboard(user.id))

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("منوی اصلی 🏠:", reply_markup=_main_menu_keyboard(update.effective_user.id))
    raise ApplicationHandlerStop

async def on_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    context.user_data[UD_STATE] = STATE_VERIF_PHOTO
    context.user_data.pop(UD_VERIFICATION_REQUEST_ID, None)
    await update.message.reply_text(
        "به بخش احراز هویت خوش آمدید.\n"
        "نکات :\n"
        "1) شماره کارت و نام صاحب کارت کاملا مشخص باشد.\n"
        "2) لطفا تاریخ اعتبار و Cvv2 کارت خود را بپوشانید!\n"
        "3) فقط با کارتی که احراز هویت میکنید میتوانید خرید انجام بدید و اگر با کارت دیگری اقدام کنید تراکنش ناموفق میشود.\n"
        "4) در صورتی که توانایی ارسال عکس از کارت را ندارید تنها راه حل ارسال عکس از کارت ملی یا شناسنامه صاحب کارت است.\n\n"
        "لطفا عکس از کارتی که میخواهید با آن خرید انجام دهید ارسال کنید.",
        reply_markup=_back_keyboard(),
    )

async def on_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("𝙢𝙤𝙗𝙞𝙣 _ 𝙨𝙞𝙡𝙫𝙚𝙧", url="https://t.me/Silverrmb")],
        [InlineKeyboardButton("ꘜ𝗞𝗔𝗦𝗘𝗕", url="https://t.me/UIDBROKEN")]
    ])
    await update.message.reply_text(
        "برای ارتباط با ادمین/پشتیبانی یا راهنمایی خرید، یکی از پشتیبان‌های زیر را انتخاب کنید:\n\n"
        "پشتیبانی سریع‌تر: لطفاً آیدی عددی + اسکرین شات مشکل/رسید + توضیح کوتاه رو هم بفرستید.",
        reply_markup=kb,
        disable_web_page_preview=True,
    )

async def on_admin_panel_cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    context.user_data[UD_STATE] = STATE_ADMIN_CANCEL_DAY
    await update.message.reply_text("چه روزی رو می‌خواید لغو/حذف کنید؟ (مثال: شنبه)", reply_markup=_reserve_days_keyboard())

async def takhfif_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    context.user_data[UD_STATE] = STATE_TAKHFIF_CODE
    await update.message.reply_text("کد تخفیف را ارسال کنید (مثال: mobin)", reply_markup=_back_keyboard())

async def account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    user_id = update.effective_user.id
    bal = await asyncio.to_thread(get_wallet_balance, user_id)
    card = await asyncio.to_thread(get_verified_card_number, user_id)
    v_status = f"تایید شده ✅ ({card})" if card else "تایید نشده ❌"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزایش اعتبار", callback_data="wallet_charge")]
    ])
    await update.message.reply_text(
        f"👛 **کیف پول و حساب کاربری شما**\n\n"
        f"🆔 آیدی شما: `{user_id}`\n"
        f"💳 وضعیت احراز هویت: {v_status}\n"
        f"💰 موجودی فعلی: {_format_toman(bal)}\n\n"
        "برای شارژ حساب روی دکمه زیر کلیک کنید👇",
        reply_markup=kb, parse_mode="Markdown"
    )

async def wallet_charge_init(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data[UD_STATE] = STATE_WALLET_AMOUNT
    await query.message.reply_text("مبلغ مورد نظر برای شارژ را به تومان وارد کنید (مثلا 100000) 💸:", reply_markup=_back_keyboard())

async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 ایجاد لینک زیر مجموعه", callback_data="ref_create")],
        [InlineKeyboardButton("📋 لیست زیر مجموعه ها", callback_data="ref_list")]
    ])
    await update.message.reply_text(
        "👥 **بخش زیرمجموعه گیری**\n\n"
        "با دعوت دوستان خود به ربات، از هر خرید آنها **۵٪ پورسانت** به کیف پول شما واریز می‌شود! 🎁",
        reply_markup=kb, parse_mode="Markdown"
    )

async def ref_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    if query.data == "ref_create":
        bot_usr = context.bot.username
        link = f"https://t.me/{bot_usr}?start=ref_{user_id}"
        await query.message.reply_text(f"لینک اختصاصی شما برای دعوت:\n\n{link}\n\nاین لینک را برای دوستان خود بفرستید! 📤")
    elif query.data == "ref_list":
        refs = await asyncio.to_thread(get_referrals, user_id)
        if not refs:
            await query.message.reply_text("شما هنوز زیرمجموعه‌ای ندارید! 😔")
            return
        kb = [[InlineKeyboardButton(f"👤 {u[1] or u[0]}", url=f"tg://user?id={u[0]}")] for u in refs]
        await query.message.reply_text(f"لیست زیرمجموعه‌های شما ({_to_fa_digits(str(len(refs)))} نفر):", reply_markup=InlineKeyboardMarkup(kb))

# ----------------- CENTRAL ROUTER (TEXT & PHOTOS) -----------------
async def central_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    user = update.effective_user
    state = context.user_data.get(UD_STATE)
    
    if msg.text == "کنسل کردن و بازگشت 🔙":
        context.user_data.clear()
        await msg.reply_text("عملیات لغو شد. به پنل بازگشتید.", reply_markup=_admin_panel_keyboard())
        return

    # Broadcast
    if state == STATE_BROADCAST and _is_admin(user.id):
        context.user_data.clear()
        users = await asyncio.to_thread(list_broadcast_user_ids)
        await msg.reply_text(f"در حال ارسال به {len(users)} نفر... ⏳")
        sent = 0
        for uid in users:
            try:
                await msg.copy(uid)
                sent += 1
                await asyncio.sleep(BROADCAST_SLEEP_SECONDS)
            except: pass
        await msg.reply_text(f"ارسال همگانی پایان یافت ✅\nموفق: {sent}", reply_markup=_admin_panel_keyboard())
        return

    # Verification Photo
    if state == STATE_VERIF_PHOTO and getattr(msg, "photo", None):
        context.user_data["verification_card_photo_file_id"] = msg.photo[-1].file_id
        context.user_data[UD_STATE] = STATE_VERIF_CARD
        await msg.reply_text("• لطفا شماره کارت خود را به صورت اعداد انگلیسی ارسال کنید\nدر صورتی که منصرف شدید دکمه بازگشت را بزنید.", reply_markup=_back_keyboard())
        return
        
    # Verification Card
    if state == STATE_VERIF_CARD and msg.text:
        card = _normalize_card_number(msg.text)
        if not card:
            await msg.reply_text("شماره کارت نامعتبر است. لطفاً فقط ۱۶ رقم انگلیسی ارسال کنید (بدون حروف).")
            return
        photo_file_id = context.user_data.get("verification_card_photo_file_id")
        username = f"@{user.username}" if user.username else None
        request_id = await asyncio.to_thread(create_verification_request, user.id, username, card, photo_file_id)
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("تایید ✅", callback_data=f"{CB_VERIF_PREFIX}{request_id}|approve")],
            [
                InlineKeyboardButton("اشتباه ❌", callback_data=f"{CB_VERIF_PREFIX}{request_id}|reject_wrong"),
                InlineKeyboardButton("کامل نیست ❌", callback_data=f"{CB_VERIF_PREFIX}{request_id}|reject_incomplete"),
            ],
        ])
        for adm in BOT_ADMIN_IDS:
            try:
                await context.bot.send_photo(adm, photo_file_id, caption=f"درخواست احراز هویت\nآیدی: {user.id}\nیوزرنیم: {username}\nکارت: {card}\nکد: {request_id}", reply_markup=kb)
            except: pass
        context.user_data.clear()
        await msg.reply_text("درخواست شما برای بررسی ارسال شد ⏳", reply_markup=_main_menu_keyboard(user.id))
        return

    # Cancel Reservation Wizard (Admin)
    if state == STATE_ADMIN_CANCEL_DAY and _is_admin(user.id) and msg.text:
        persian_weekday = DAY_TO_PERSIAN_WEEKDAY.get(msg.text.strip())
        if persian_weekday is None:
            await msg.reply_text("روز نامعتبر است. یکی از روزهای هفته مثل «شنبه» را ارسال کنید.")
            return
        now = datetime.now(TZ)
        target_date = _next_date_for_persian_weekday(int(persian_weekday), now)
        context.user_data[STATE_ADMIN_CANCEL_DAY] = target_date.isoformat()
        context.user_data[UD_STATE] = STATE_ADMIN_CANCEL_TIME
        jdate = jdatetime.date.fromgregorian(date=target_date)
        date_str = f"{jdate.year:04d}/{jdate.month:02d}/{jdate.day:02d}".translate(PERSIAN_DIGITS)
        await msg.reply_text(f"اوکی. برای تاریخ {date_str} چه ساعتی رو می‌خواید لغو کنید؟ (مثال: 20:30)", reply_markup=_back_keyboard())
        return

    if state == STATE_ADMIN_CANCEL_TIME and _is_admin(user.id) and msg.text:
        date_iso = context.user_data.get(STATE_ADMIN_CANCEL_DAY)
        hhmm = _normalize_hhmm(msg.text)
        if not hhmm:
            await msg.reply_text("ساعت نامعتبر است. فرمت صحیح مثل 20:30")
            return
        target_date = datetime.fromisoformat(date_iso).date()
        hh, mm = map(int, hhmm.split(":", 1))
        slot_dt = datetime.combine(target_date, time(hh, mm), tzinfo=TZ)
        affected = await asyncio.to_thread(cancel_booked_reservation_by_reserved_at, slot_dt)
        context.user_data.clear()
        if affected <= 0:
            await msg.reply_text("برای این روز/ساعت رزرو قطعی پیدا نشد (یا قبلاً لغو شده).", reply_markup=_admin_panel_keyboard())
        else:
            jdate = jdatetime.date.fromgregorian(date=slot_dt.date())
            date_str = f"{jdate.year:04d}/{jdate.month:02d}/{jdate.day:02d}".translate(PERSIAN_DIGITS)
            time_str = slot_dt.strftime("%H:%M").translate(PERSIAN_DIGITS)
            await msg.reply_text(f"رزرو {date_str} - {time_str} با موفقیت لغو شد ✅\nالان این تایم برای کاربران آزاد نمایش داده می‌شود.", reply_markup=_admin_panel_keyboard())
        return

    # Takhfif Wizard (Admin)
    if state == STATE_TAKHFIF_CODE and _is_admin(user.id) and msg.text:
        if not re.fullmatch(r"[A-Za-z0-9_\-]{2,64}", msg.text):
            await msg.reply_text("کد نامعتبر است. فقط حروف/عدد انگلیسی و _ یا - مجاز است.")
            return
        context.user_data['t_code'] = normalize_discount_code(msg.text)
        context.user_data[UD_STATE] = STATE_TAKHFIF_USES
        await msg.reply_text("این کد چند بار قابل استفاده باشد؟ (مثال: 5)")
        return
        
    if state == STATE_TAKHFIF_USES and _is_admin(user.id) and msg.text:
        if not msg.text.isdigit() or int(msg.text) <= 0:
            await msg.reply_text("عدد نامعتبر است.")
            return
        context.user_data['t_uses'] = int(msg.text)
        context.user_data[UD_STATE] = STATE_TAKHFIF_DUR
        await msg.reply_text("مدت اعتبار را ارسال کنید (مثال: 20 روز | 20 ساعت | 20 دقیقه)")
        return

    if state == STATE_TAKHFIF_DUR and _is_admin(user.id) and msg.text:
        delta = _parse_duration_to_timedelta(msg.text)
        if not delta:
            await msg.reply_text("فرمت مدت نامعتبر است.")
            return
        now_utc_dt = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        context.user_data['t_dur'] = (now_utc_dt + delta).replace(tzinfo=None).isoformat(timespec="seconds")
        context.user_data[UD_STATE] = STATE_TAKHFIF_AMT
        await msg.reply_text("مبلغ تخفیف چند تومان باشد؟ (مثال: 100000)")
        return

    if state == STATE_TAKHFIF_AMT and _is_admin(user.id) and msg.text:
        amt = _parse_toman_amount(msg.text)
        if not amt:
            await msg.reply_text("مبلغ نامعتبر است.")
            return
        context.user_data['t_amt'] = amt
        context.user_data[UD_STATE] = STATE_TAKHFIF_PKG
        pkgs = await asyncio.to_thread(get_packages)
        kb = []
        row = []
        for c, _, _ in pkgs:
            row.append(InlineKeyboardButton(f"{c} پخشی", callback_data=f"{CB_TAKHFIF_PKG_PREFIX}{c}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row: kb.append(row)
        await msg.reply_text("این تخفیف روی کدام پکیج اعمال شود؟", reply_markup=InlineKeyboardMarkup(kb))
        return

    # Admin Edits Daily Limit
    if state == STATE_EDIT_DAILY_LIMIT and _is_admin(user.id) and msg.text:
        new_limit = _parse_daily_limit(msg.text)
        if new_limit <= 0:
            await msg.reply_text("لطفاً یک عدد معتبر ارسال کنید.")
            return
        await asyncio.to_thread(set_setting, "daily_limit", str(new_limit))
        context.user_data.clear()
        await msg.reply_text(f"محدودیت روزانه با موفقیت به {new_limit} تغییر یافت ✅", reply_markup=_admin_panel_keyboard())
        return

    # Wallet Charge Amount
    if state == STATE_WALLET_AMOUNT and msg.text:
        amt = _parse_toman_amount(msg.text)
        if not amt:
            await msg.reply_text("❌ مبلغ نامعتبر! لطفا عدد لاتین بفرستید.")
            return
        
        card = await asyncio.to_thread(get_verified_card_number, user.id)
        if not card:
            context.user_data[UD_STATE] = STATE_VERIF_PHOTO
            await msg.reply_text("⚠️ شما هنوز احراز هویت نکرده‌اید! ابتدا لطفا عکس کارت بانکی خود را ارسال کنید:")
            return
        
        context.user_data['temp_wallet_amt'] = amt
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("واریز کردم ✅", callback_data="wallet_paid")]])
        card_text = get_setting("card_number_text", DEFAULT_CARD_TEXT)
        await msg.reply_text(f"مبلغ درخواستی: {_format_toman(amt)}\n\n{card_text}", reply_markup=kb)
        context.user_data[UD_STATE] = None
        return

    # Wallet Charge Receipt
    if state == STATE_WALLET_RECEIPT and getattr(msg, "photo", None):
        amt = context.user_data.get('temp_wallet_amt', 0)
        req_id = await asyncio.to_thread(create_wallet_req, user.id, amt, msg.photo[-1].file_id)
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("تایید ✅", callback_data=f"wal_ok|{req_id}"), InlineKeyboardButton("رد ❌", callback_data=f"wal_no|{req_id}")]
        ])
        card = await asyncio.to_thread(get_verified_card_number, user.id)
        for adm in BOT_ADMIN_IDS:
            try:
                await context.bot.send_photo(adm, msg.photo[-1].file_id, caption=f"درخواست شارژ کیف پول 👛\nآیدی: {user.id}\nمبلغ: {_format_toman(amt)}\nکارت: {card}", reply_markup=kb)
            except: pass
            
        context.user_data.clear()
        await msg.reply_text("فیش شما ارسال شد و در انتظار تایید ادمین است ⏳", reply_markup=_main_menu_keyboard(user.id))
        return

    # --- RESERVATION FLOW (Coupon & Receipt) ---
    if state == STATE_PAY_COUPON and msg.text:
        res_id = context.user_data.get(UD_PAYMENT_RESERVATION_ID)
        if not res_id:
            await msg.reply_text("خطا در روند پرداخت. دوباره تلاش کنید: /start")
            return
            
        code = msg.text.strip()
        pkg_cnt = context.user_data.get('res_pkg')
        now_utc = datetime.utcnow().isoformat(timespec="seconds")
        ok, reason, percent, amount_toman, req_pkg = await asyncio.to_thread(can_use_discount_code, code, now_utc, pkg_cnt)
        if not ok:
            if reason == "expired": await msg.reply_text("این کد تخفیف منقضی شده است.")
            elif reason == "used_up": await msg.reply_text("سهمیه این کد تخفیف تمام شده است.")
            elif reason == "wrong_package": await msg.reply_text(f"این کد فقط برای پکیج {req_pkg} پخشی است.")
            else: await msg.reply_text("این کد تخفیف معتبر نیست.")
            return

        context.user_data['pay_coupon'] = normalize_discount_code(code)
        context.user_data['pay_percent'] = percent or 0
        context.user_data['pay_amount'] = amount_toman
        context.user_data[UD_STATE] = STATE_PAY_RECEIPT

        base_price = context.user_data.get('res_price', 0)
        final_price = _apply_discount_amount(base_price, percent, amount_toman)

        discount_line = f"کد تخفیف شما ثبت شد: {code} ({_format_toman(amount_toman)})\n" if amount_toman else f"کد تخفیف شما ثبت شد: {code} ({percent}٪)\n"
        card_text = get_setting("card_number_text", DEFAULT_CARD_TEXT)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("واریز کردم ✅", callback_data="res_paid_btn")]])
        await msg.reply_text(f"{discount_line}مبلغ نهایی قابل پرداخت: {_format_toman(final_price)}\n\n{card_text}", reply_markup=kb)
        return

    if state == STATE_PAY_RECEIPT and getattr(msg, "photo", None):
        res_id = context.user_data.get(UD_PAYMENT_RESERVATION_ID)
        if not res_id:
            await msg.reply_text("خطا در روند پرداخت. دوباره تلاش کنید: /start")
            return
            
        receipt_file_id = msg.photo[-1].file_id
        username = f"@{user.username}" if user.username else None
        
        coupon = context.user_data.get('pay_coupon')
        coupon_percent = context.user_data.get('pay_percent')
        coupon_amount_toman = context.user_data.get('pay_amount')
        package_count = context.user_data.get('res_pkg')
        base_price = context.user_data.get('res_price', 0)
        final_price = _apply_discount_amount(base_price, coupon_percent, coupon_amount_toman)

        verified_card = await asyncio.to_thread(get_verified_card_number, user.id)
        payment_id = await asyncio.to_thread(create_payment_request, res_id, user.id, username, verified_card or "-", coupon, coupon_percent, coupon_amount_toman, package_count, receipt_file_id)

        caption = (
            "خرید کاربر\n\n"
            f"آیدی عددی: {user.id}\n"
            f"یوزرنیم: {username or 'ندارد'}\n"
            f"شماره کارت: {verified_card or '-'}\n"
            f"پکیج: {package_count} پخشی\n"
            f"مبلغ پایه: {_format_toman(base_price)}\n"
            f"مبلغ نهایی: {_format_toman(final_price)}\n"
            f"کد پرداخت: {payment_id}"
        )
        if coupon: caption += f"\nکد تخفیف: {coupon}"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("تایید ✅", callback_data=f"{CB_PAYMENT_PREFIX}{payment_id}|approve")],
            [InlineKeyboardButton("رد ❌", callback_data=f"{CB_PAYMENT_PREFIX}{payment_id}|reject")],
        ])

        for adm in BOT_ADMIN_IDS:
            try: await context.bot.send_photo(adm, receipt_file_id, caption=caption, reply_markup=kb)
            except: pass

        context.user_data.clear()
        await msg.reply_text("فیش شما ارسال شد و در حال بررسی است.", reply_markup=_main_menu_keyboard(user.id))
        return

    # Banner After Approve
    awaiting = context.bot_data.get(BOTDATA_USER_AWAIT_BANNER, {})
    if awaiting.get(str(user.id)):
        res_id = awaiting.pop(str(user.id))
        username = f"@{user.username}" if user.username else None
        group_link, promo_photo_file_id = None, None
        if msg.text and msg.text.strip().lower().startswith("http"): group_link = msg.text.strip()
        if getattr(msg, "photo", None): promo_photo_file_id = msg.photo[-1].file_id

        await asyncio.to_thread(update_reservation_promo, res_id, username, group_link, promo_photo_file_id)

        for adm in BOT_ADMIN_IDS:
            try: await context.bot.forward_message(adm, msg.chat_id, msg.message_id)
            except: pass

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("دارم ✅", callback_data=f"{CB_DEST_PREFIX}{res_id}|has"), InlineKeyboardButton("ندارم ❌", callback_data=f"{CB_DEST_PREFIX}{res_id}|no")]
        ])
        await msg.reply_text("کاربر عزیز لینک گروه مقصد رو ارسال کنید...", reply_markup=kb)
        return

    # Destination links
    if state == STATE_DEST_LINKS and msg.text:
        res_id = context.user_data.get(UD_DEST_RESERVATION_ID)
        if msg.text == DEST_FINISH_TEXT:
            links_list = context.user_data.get(UD_DEST_LINKS_LIST, [])
            links_text = "\n".join(links_list)
            await asyncio.to_thread(update_reservation_destination_links, res_id, links_text)
            
            for adm in BOT_ADMIN_IDS:
                try: await context.bot.send_message(adm, f"اطلاعات رزرو:\nکد رزرو: {res_id}\n\nلینک‌های مقصد:\n{links_text}")
                except: pass
                
            context.user_data.clear()
            await msg.reply_text("ثبت شد.", reply_markup=_main_menu_keyboard(user.id))
            return
        
        lst = context.user_data.get(UD_DEST_LINKS_LIST, [])
        lst.append(msg.text.strip())
        context.user_data[UD_DEST_LINKS_LIST] = lst
        await msg.reply_text("لینک بعدی رو ارسال کن یا دکمه پایان رو بزنید", reply_markup=_finish_keyboard())
        return

    if state == STATE_DEST_DESC and msg.text:
        res_id = context.user_data.get(UD_DEST_RESERVATION_ID)
        saved_text = f"توضیحات مقصد: {msg.text.strip()}"
        await asyncio.to_thread(update_reservation_destination_links, res_id, saved_text)
        
        for adm in BOT_ADMIN_IDS:
            try: await context.bot.send_message(adm, f"اطلاعات رزرو:\nکد رزرو: {res_id}\n\n{saved_text}")
            except: pass
            
        context.user_data.clear()
        await msg.reply_text("با موفقیت ثبت شد.", reply_markup=_main_menu_keyboard(user.id))
        return

    # Admin Settings Edits (Texts)
    if state == STATE_EDIT_WELCOME and _is_admin(user.id) and msg.text:
        context.user_data['temp_edit'] = msg.text
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("بله 🟢", callback_data="edit_ok|welcome"), InlineKeyboardButton("خیر 🔴", callback_data="edit_no")]])
        await msg.reply_text(f"آیا متن زیر تایید میشود؟\n\n{msg.text}", reply_markup=kb)
        return
    if state == STATE_EDIT_CARD and _is_admin(user.id) and msg.text:
        context.user_data['temp_edit'] = msg.text
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("بله 🟢", callback_data="edit_ok|card"), InlineKeyboardButton("خیر 🔴", callback_data="edit_no")]])
        await msg.reply_text(f"آیا متن زیر تایید میشود؟\n\n{msg.text}", reply_markup=kb)
        return
    if state == STATE_EDIT_RATES and _is_admin(user.id) and msg.text:
        context.user_data['temp_edit'] = msg.text
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("بله 🟢", callback_data="edit_ok|rates"), InlineKeyboardButton("خیر 🔴", callback_data="edit_no")]])
        await msg.reply_text(f"آیا متن زیر تایید میشود؟\n\n{msg.text}", reply_markup=kb)
        return
    if state == STATE_EDIT_PKG_PRICE and _is_admin(user.id) and msg.text:
        try:
            val = int(msg.text.translate(FA_TO_EN_DIGITS))
            pkg_cnt = context.user_data['temp_pkg_cnt']
            await asyncio.to_thread(update_package, pkg_cnt, price=val)
            context.user_data.clear()
            await msg.reply_text("قیمت با موفقیت آپدیت شد ✅", reply_markup=_settings_menu_keyboard())
        except:
            await msg.reply_text("عدد نامعتبر!")
        return

async def admin_edits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "edit_no":
        context.user_data.clear()
        await query.edit_message_text("عملیات لغو شد ❌")
        return
    if data.startswith("edit_ok|"):
        key = data.split("|")[1]
        val = context.user_data.get('temp_edit')
        db_key = "welcome_text" if key=="welcome" else ("card_number_text" if key=="card" else "rates_text")
        await asyncio.to_thread(set_setting, db_key, val)
        context.user_data.clear()
        await query.edit_message_text("تغییرات با موفقیت ذخیره شد ✅")

async def wallet_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    _, req_id = data.split("|")
    req_id = int(req_id)
    req = await asyncio.to_thread(get_wallet_req, req_id)
    if not req or req[2] != 'pending':
        await query.answer("قبلا بررسی شده!")
        return
    
    if data.startswith("wal_ok"):
        await asyncio.to_thread(add_wallet_balance, req[0], req[1])
        await asyncio.to_thread(update_wallet_req, req_id, 'approved')
        await query.edit_message_caption(caption=query.message.caption + "\n\nتایید شد ✅")
        try: await context.bot.send_message(req[0], f"مبلغ {_format_toman(req[1])} با موفقیت به کیف پول شما اضافه شد ✅")
        except: pass
    else:
        await asyncio.to_thread(update_wallet_req, req_id, 'rejected')
        await query.edit_message_caption(caption=query.message.caption + "\n\nرد شد ❌")
        try: await context.bot.send_message(req[0], f"درخواست شارژ کیف پول شما رد شد ❌")
        except: pass

# Admin Stats Pagination
async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, offset=0):
    tu, a24, a7d, a30, rb, pa, va = await asyncio.to_thread(get_admin_stats_detailed)
    text = (
        "📊 **آمار خفن ربات**\n\n"
        f"👥 کل کاربران: `{tu}`\n"
        f"🔥 فعال ۲۴ ساعت: `{a24}`\n"
        f"📅 فعال ۷ روز: `{a7d}`\n"
        f"🗓 فعال ۳۰ روز: `{a30}`\n\n"
        f"✅ رزروهای قطعی: `{rb}`\n"
        f"💳 پرداخت موفق: `{pa}`\n"
        f"🪪 احراز هویت تایید شده: `{va}`\n\n"
        "👇 لیست کاربران:"
    )
    
    limit = 10
    with sqlite3.connect(_db_path()) as con:
        users = con.execute("SELECT user_id, username FROM users ORDER BY first_seen_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    
    kb = []
    for u in users:
        name = u[1] if u[1] else str(u[0])
        kb.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"adm_usr|{u[0]}")])
    
    nav = []
    if offset > 0: nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"adm_pg|{offset-limit}"))
    if len(users) == limit: nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"adm_pg|{offset+limit}"))
    if nav: kb.append(nav)

    if update.callback_query:
        try: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        except: pass
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def admin_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.split("|")[1])
    
    with sqlite3.connect(_db_path()) as con:
        u = con.execute("SELECT first_seen_at, wallet_balance, referrer_id FROM users WHERE user_id=?", (uid,)).fetchone()
        rb = con.execute("SELECT COUNT(*) FROM reservations WHERE user_id=? AND status='booked'", (uid,)).fetchone()[0]
        card = con.execute("SELECT card_number FROM verified_cards WHERE user_id=?", (uid,)).fetchone()
    
    card_str = f"✅ تایید شده ({card[0]})" if card else "❌ تایید نشده"
    
    text = (
        f"🔍 **پروفایل حرفه‌ای کاربر**\n\n"
        f"🆔 آیدی عددی: `{uid}`\n"
        f"🪪 احراز هویت: {card_str}\n"
        f"👛 موجودی کیف پول: {_format_toman(u[1])}\n"
        f"✅ تعداد رزروهای موفق: `{rb}`\n"
        f"📅 تاریخ استارت: `{_format_seen_at(u[0])}`\n"
    )
    
    try:
        photos = await context.bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count > 0:
            await query.message.reply_photo(photos.photos[0][-1].file_id, caption=text, parse_mode="Markdown")
        else:
            await query.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await query.message.reply_text(text, parse_mode="Markdown")

async def inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pkgs = await asyncio.to_thread(get_packages)
    kb = []
    for count, price, active in pkgs:
        status = "✅" if active else "❌"
        kb.append([
            InlineKeyboardButton(f"{count} پخشی", callback_data="noop"),
            InlineKeyboardButton(status, callback_data=f"pkg_tog|{count}"),
            InlineKeyboardButton(f"نرخ ({_format_toman(price)}) 💰", callback_data=f"pkg_rate|{count}")
        ])
    await update.message.reply_text("📦 **ویرایش موجودی ها و نرخ پکیج ها**\nروی آیکون برای فعال/غیرفعال سازی کلیک کنید:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def inventory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, count = query.data.split("|")
    count = int(count)
    if action == "pkg_tog":
        await asyncio.to_thread(update_package, count, toggle=True)
        pkgs = await asyncio.to_thread(get_packages)
        kb = []
        for c, p, a in pkgs:
            kb.append([
                InlineKeyboardButton(f"{c} پخشی", callback_data="noop"),
                InlineKeyboardButton("✅" if a else "❌", callback_data=f"pkg_tog|{c}"),
                InlineKeyboardButton(f"نرخ ({_format_toman(p)}) 💰", callback_data=f"pkg_rate|{c}")
            ])
        await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
    elif action == "pkg_rate":
        context.user_data[UD_STATE] = STATE_EDIT_PKG_PRICE
        context.user_data['temp_pkg_cnt'] = count
        await query.message.reply_text(f"💰 نرخ جدید برای پکیج {count} پخشی را به تومان ارسال کنید (فقط عدد):", reply_markup=_back_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "پنل مدیریت 🛠" and _is_admin(user_id):
        await update.message.reply_text("پنل مدیریت باز شد:", reply_markup=_admin_panel_keyboard())
    elif text == "⚙️ تنظیمات و ویرایش" and _is_admin(user_id):
        await update.message.reply_text("بخش تنظیمات:", reply_markup=_settings_menu_keyboard())
    elif text == "📝 ویرایش خوش امدگویی" and _is_admin(user_id):
        context.user_data[UD_STATE] = STATE_EDIT_WELCOME
        cur = get_setting("welcome_text", DEFAULT_WELCOME_TEXT)
        await update.message.reply_text(f"متن فعلی خوش امدگویی:\n\n{cur}\n\nمتن جدید را ارسال کنید:", reply_markup=_back_keyboard())
    elif text == "💳 ویرایش شماره کارت" and _is_admin(user_id):
        context.user_data[UD_STATE] = STATE_EDIT_CARD
        cur = get_setting("card_number_text", DEFAULT_CARD_TEXT)
        await update.message.reply_text(f"متن فعلی کارت:\n\n{cur}\n\nمتن جدید را ارسال کنید:", reply_markup=_back_keyboard())
    elif text == "📜 ویرایش متن نرخ" and _is_admin(user_id):
        context.user_data[UD_STATE] = STATE_EDIT_RATES
        cur = get_setting("rates_text", DEFAULT_RATES_TEXT)
        await update.message.reply_text(f"متن فعلی نرخ:\n\n{cur}\n\nمتن جدید را ارسال کنید:", reply_markup=_back_keyboard())
    elif text == "📦 ویرایش موجودی ها" and _is_admin(user_id):
        await inventory_menu(update, context)
    elif text == "📊 ویرایش محدودیت روزانه" and _is_admin(user_id):
        context.user_data[UD_STATE] = STATE_EDIT_DAILY_LIMIT
        cur = get_daily_limit()
        await update.message.reply_text(f"محدودیت فعلی: {cur}\n\nمحدودیت جدید را به صورت عدد (مثلاً 3000) ارسال کنید:", reply_markup=_back_keyboard())
    elif text == "📣 همگانی" and _is_admin(user_id):
        context.user_data[UD_STATE] = STATE_BROADCAST
        await update.message.reply_text("پیام خود را بفرستید. برای لغو روی کنسل کلیک کنید:", reply_markup=_cancel_broadcast_keyboard())
    elif text == "📊 آمار" and _is_admin(user_id):
        await show_admin_stats(update, context)
    elif text == "🎟️ کد تخفیف" and _is_admin(user_id):
        await takhfif_start(update, context)
    elif text == "🗑️ حذف رزرو" and _is_admin(user_id):
        await on_admin_panel_cancel_reservation(update, context)
    elif text == "🪪 احراز هویت":
        await on_verification(update, context)
    elif text == "📞 ارتباط با ادمین":
        await on_contact_admin(update, context)
    elif text == "💳 حساب کاربری":
        await account_menu(update, context)
    elif text == "👥 زیر مجموعه گیری":
        await referral_menu(update, context)
    elif text == "📜 نرخ":
        await update.message.reply_text(get_setting("rates_text", DEFAULT_RATES_TEXT))
    elif text in ["بازگشت", "🔙 بازگشت به پنل"]:
        await handle_back(update, context)
    elif text == "⏰ رزرو تایم":
        await reserve_day_menu(update, context)
    elif text in [DAY_SAT, DAY_SUN, DAY_MON, DAY_TUE, DAY_WED, DAY_THU, DAY_FRI]:
        await on_day_selected(update, context)
    else:
        await central_router(update, context)

# Reservation Time Handling
async def reserve_day_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    await update.message.reply_text("روز مورد نظر برای رزرو را انتخاب کنید:", reply_markup=_reserve_days_keyboard())

async def on_day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_membership_gate(update, context): return
    persian_weekday = DAY_TO_PERSIAN_WEEKDAY.get(update.message.text.strip())
    if persian_weekday is None: return
    
    msg = await update.message.reply_text("در حال بارگذاری تایم ها...", reply_markup=_back_keyboard())
    try:
        target_date = _next_date_for_persian_weekday(persian_weekday, datetime.now(TZ))
        
        await asyncio.to_thread(release_stale_reservations)
        rows = []
        for t in _time_slots():
            dt = datetime.combine(target_date, t, tzinfo=TZ)
            reserved = await asyncio.to_thread(is_slot_reserved, dt)
            label = f"{dt.strftime('%H:%M').translate(PERSIAN_DIGITS)} {'❌' if reserved else '✅'}"
            rows.append((label, f"{CB_SLOT_PREFIX}{target_date.isoformat()}|{t.strftime('%H:%M')}"))

        kb = []
        for i in range(0, len(rows), 2):
            pair = rows[i: i+2]
            kb.append([InlineKeyboardButton(pair[0][0], callback_data=pair[0][1])] + ([InlineKeyboardButton(pair[1][0], callback_data=pair[1][1])] if len(pair)>1 else []))

        dl = await asyncio.to_thread(get_daily_limit)
        booked_pakhsh = await asyncio.to_thread(sum_booked_pakhsh, target_date.isoformat())
        remain = max(0, dl - booked_pakhsh)
        jdate = jdatetime.date.fromgregorian(date=target_date)
        date_str = f"{jdate.year:04d}/{jdate.month:02d}/{jdate.day:02d}".translate(PERSIAN_DIGITS)

        txt = (
            f"رزرو تایم\n"
            f"محدودیت روزانه: {_to_fa_digits(str(dl))} | رزرو شده: {_to_fa_digits(str(booked_pakhsh))} | باقیمانده: {_to_fa_digits(str(remain))}\n\n"
            f"تاریخ: {date_str}\n\n"
            f"✅ آزاد | ❌ رزرو شده"
        )
        await msg.delete()
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        logger.error(f"Error in on_day_selected: {e}")
        await msg.edit_text("خطایی رخ داد.")

async def reserve_slots_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # 1. Select Slot
    if query.data.startswith(CB_SLOT_PREFIX):
        user = update.effective_user
        _, date_iso, hhmm = query.data.split("|", 2)
        target_date = datetime.fromisoformat(date_iso).date()
        hh, mm = map(int, hhmm.split(":", 1))
        slot_dt = datetime.combine(target_date, time(hh, mm), tzinfo=TZ)
        
        verified_card = await asyncio.to_thread(get_verified_card_number, user.id)
        if not verified_card:
            await query.answer("ابتدا احراز هویت را انجام دهید.", show_alert=True)
            return

        context.user_data[UD_PENDING_SLOT_ISO] = slot_dt.isoformat(timespec="seconds")
        pkgs = await asyncio.to_thread(get_active_packages)
        kb_pkg = []
        row = []
        for c, _ in pkgs:
            row.append(InlineKeyboardButton(f"{c} پخشی", callback_data=f"{CB_PACKAGE_PREFIX}{date_iso}|{hhmm}|{c}"))
            if len(row) == 2:
                kb_pkg.append(row)
                row = []
        if row: kb_pkg.append(row)
        await query.edit_message_text(f"چه مقدار پخشی نیاز دارید؟", reply_markup=InlineKeyboardMarkup(kb_pkg))
    
    # 2. Select Package
    elif query.data.startswith(CB_PACKAGE_PREFIX):
        user = update.effective_user
        _, date_iso, hhmm, count_s = query.data.split("|", 3)
        count = int(count_s)
        target_date = datetime.fromisoformat(date_iso).date()
        hh, mm = map(int, hhmm.split(":", 1))
        slot_dt = datetime.combine(target_date, time(hh, mm), tzinfo=TZ)
        
        dl = await asyncio.to_thread(get_daily_limit)
        booked_pakhsh = await asyncio.to_thread(sum_booked_pakhsh, target_date.isoformat())
        if booked_pakhsh + count > dl:
            await query.answer(f"ظرفیت پخشی تکمیل است.\nباقیمانده: {max(0, dl - booked_pakhsh)}", show_alert=True)
            return

        reservation_id = await asyncio.to_thread(try_hold_slot_pending_payment, user.id, slot_dt)
        if not reservation_id:
            await query.answer("این تایم همین الان رزرو شد.", show_alert=True)
            return

        price = await asyncio.to_thread(get_package_price, count)
        context.user_data['res_pkg'] = count
        context.user_data['res_price'] = price
        context.user_data[UD_PAYMENT_RESERVATION_ID] = reservation_id

        bal = await asyncio.to_thread(get_wallet_balance, user.id)
        txt = f"💰 مبلغ پایه: {_format_toman(price)}\n\nروش پرداخت را انتخاب کنید:"
        
        kb = []
        if bal >= price:
            kb.append([InlineKeyboardButton("💳 پرداخت از کیف پول", callback_data="payw_yes")])
        kb.append([InlineKeyboardButton("💳 کارت به کارت", callback_data="payw_no")])
        
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        
    # 3A. Wallet Flow
    elif query.data == "payw_yes":
        user_id = update.effective_user.id
        res_id = context.user_data.get(UD_PAYMENT_RESERVATION_ID)
        price = context.user_data.get('res_price', 0)
        bal = await asyncio.to_thread(get_wallet_balance, user_id)
        if bal < price:
            await query.answer("موجودی کافی نیست!", show_alert=True)
            return
        
        await asyncio.to_thread(add_wallet_balance, user_id, -price)
        await asyncio.to_thread(try_book_reservation, res_id)
        await asyncio.to_thread(process_referral_reward, user_id, price, context.bot)
        
        awaiting = context.bot_data.setdefault(BOTDATA_USER_AWAIT_BANNER, {})
        awaiting[str(user_id)] = res_id
        await query.edit_message_text("✅ پرداخت از کیف پول انجام شد. تایم شما قطعی است.\n\nلطفا بنر تبلیغاتی خود را ارسال کنید:")
        
    # 3B. Card Flow -> Ask Discount (Original Flow)
    elif query.data == "payw_no":
        res_id = context.user_data.get(UD_PAYMENT_RESERVATION_ID)
        kb_discount = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("بله ✅", callback_data=f"{CB_DISCOUNT_PREFIX}{res_id}|yes"),
                InlineKeyboardButton("خیر ❌", callback_data=f"{CB_DISCOUNT_PREFIX}{res_id}|no")
            ]
        ])
        await query.edit_message_text("آیا کد تخفیف دارید؟", reply_markup=kb_discount)

async def on_discount_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        rest = query.data[len(CB_DISCOUNT_PREFIX) :]
        res_id_str, choice = rest.split("|", 1)
        reservation_id = int(res_id_str)
    except Exception:
        await query.answer("داده نامعتبر است.", show_alert=True)
        return

    if choice == "yes":
        context.user_data[UD_STATE] = STATE_PAY_COUPON
        context.user_data[UD_PAYMENT_RESERVATION_ID] = reservation_id
        await query.edit_message_text("کد تخفیف خود را ارسال کنید (اعداد/حروف انگلیسی):")
        
    elif choice == "no":
        context.user_data[UD_STATE] = STATE_PAY_RECEIPT
        context.user_data[UD_PAYMENT_RESERVATION_ID] = reservation_id
        price = context.user_data.get('res_price', 0)
        card_text = get_setting("card_number_text", DEFAULT_CARD_TEXT)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("واریز کردم ✅", callback_data="res_paid_btn")]])
        await query.edit_message_text(f"مبلغ: {_format_toman(price)}\n\n{card_text}", reply_markup=kb)

async def on_res_paid_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data[UD_STATE] = STATE_PAY_RECEIPT
    await query.message.reply_text("📸 لطفاً عکس فیش واریزی خود را ارسال کنید:")

async def on_verification_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    
    try:
        _, rest = query.data.split("verif|", 1)
        req_id_str, action = rest.split("|", 1)
        request_id = int(req_id_str)
    except: return

    req = await asyncio.to_thread(get_verification_request, request_id)
    if not req or req[3] != "pending":
        await query.answer("این درخواست قبلاً بررسی شده.", show_alert=True)
        return

    if action == "approve":
        await asyncio.to_thread(set_verification_status, request_id, "approved", update.effective_user.id, None)
        await asyncio.to_thread(upsert_verified_card, req[0], req[1], req[2], update.effective_user.id)
        try: await context.bot.send_message(req[0], f"• درخواست احراز هویت کارت ( {req[2]} ) تایید شد. هم اکنون میتوانید رزرو تایم انجام دهید.")
        except: pass
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\nوضعیت: تایید شد ✅", reply_markup=None)
    elif action == "reject_wrong":
        await asyncio.to_thread(set_verification_status, request_id, "rejected", update.effective_user.id, "wrong")
        try: await context.bot.send_message(req[0], f"• درخواست احراز هویت کارت ( {req[2]} ) به دلیل اشتباه بودن عکس رد شد.")
        except: pass
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\nوضعیت: رد شد (اشتباه) ❌", reply_markup=None)
    elif action == "reject_incomplete":
        await asyncio.to_thread(set_verification_status, request_id, "rejected", update.effective_user.id, "incomplete")
        try: await context.bot.send_message(req[0], f"• درخواست احراز هویت کارت ( {req[2]} ) به دلیل کامل نبودن رد شد.")
        except: pass
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\nوضعیت: رد شد (کامل نیست) ❌", reply_markup=None)

async def payment_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    
    try:
        rest = query.data[len(CB_PAYMENT_PREFIX) :]
        pay_id_str, action = rest.split("|", 1)
        payment_id = int(pay_id_str)
    except: return

    pay = await asyncio.to_thread(get_payment_request, payment_id)
    if not pay or pay[10] != "pending":
        await query.answer("این پرداخت قبلاً بررسی شده.", show_alert=True)
        return

    if action == "approve":
        booked_ok = await asyncio.to_thread(try_book_reservation, pay[1])
        if not booked_ok:
            await asyncio.to_thread(set_payment_status, payment_id, "rejected", update.effective_user.id, "تایم قبلاً رزرو شده است")
            await asyncio.to_thread(set_reservation_status, pay[1], "cancelled")
            try: await context.bot.send_message(pay[2], "پرداخت شما رد شد ❌\nدلیل: این تایم قبل از تایید شما رزرو شده است.")
            except: pass
            await query.edit_message_caption(caption=(query.message.caption or "") + "\n\nرد شد ❌ (تایم پر بود)", reply_markup=None)
            return

        await asyncio.to_thread(set_payment_status, payment_id, "approved", update.effective_user.id, None)
        if pay[5]: 
            now_utc = datetime.utcnow().isoformat(timespec="seconds")
            await asyncio.to_thread(consume_discount_code, pay[5], now_utc)

        await asyncio.to_thread(process_referral_reward, pay[2], pay[8] or 0, context.bot)

        awaiting = context.bot_data.setdefault(BOTDATA_USER_AWAIT_BANNER, {})
        awaiting[str(pay[2])] = pay[1]
        try: await context.bot.send_message(pay[2], "پرداخت تایید شد ✅\nلطفاً بنر خود را ارسال کنید:")
        except: pass
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\nوضعیت: تایید شد ✅", reply_markup=None)

    elif action == "reject":
        pending = context.bot_data.setdefault(BOTDATA_OWNER_PENDING_REJECT, {})
        pending[str(update.effective_user.id)] = payment_id
        await context.bot.send_message(update.effective_user.id, "دلیل رد کردن واریزی را بنویسید:")

async def on_owner_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    actor = update.effective_user
    pending = context.bot_data.get(BOTDATA_OWNER_PENDING_REJECT, {})
    payment_id = pending.get(str(actor.id))
    if not payment_id: return

    reason = msg.text.strip()
    pay = await asyncio.to_thread(get_payment_request, int(payment_id))
    if pay and pay[10] == "pending":
        await asyncio.to_thread(set_payment_status, int(payment_id), "rejected", actor.id, reason)
        await asyncio.to_thread(set_reservation_status, pay[1], "cancelled")
        try: await context.bot.send_message(pay[2], f"پرداخت شما رد شد ❌\nدلیل: {reason}")
        except: pass
    pending.pop(str(actor.id), None)
    await msg.reply_text("دلیل ثبت و به کاربر ارسال شد.")

async def on_dest_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        rest = query.data[len(CB_DEST_PREFIX):]
        res_id_str, choice = rest.split("|", 1)
        res_id = int(res_id_str)
    except: return

    if choice == "no":
        context.user_data[UD_STATE] = STATE_DEST_DESC
        context.user_data[UD_DEST_RESERVATION_ID] = res_id
        await query.edit_message_text("یک توضیح خلاصه بفرستید (مثلا رنج سنی):")
    elif choice == "has":
        context.user_data[UD_STATE] = STATE_DEST_LINKS
        context.user_data[UD_DEST_RESERVATION_ID] = res_id
        context.user_data[UD_DEST_LINKS_LIST] = []
        await query.edit_message_text("لینک گروه مقصد رو بفرستید (هر لینک را جداگانه بفرستید و در آخر پایان را بزنید):")
        await context.bot.send_message(update.effective_chat.id, "منتظر لینک...", reply_markup=_finish_keyboard())

async def on_takhfif_package_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    if context.user_data.get(UD_STATE) != STATE_TAKHFIF_PKG: return
    
    try: pkg = int(query.data.split("|")[1])
    except: return
        
    code = context.user_data.get('t_code')
    max_uses = context.user_data.get('t_uses')
    expires_at = context.user_data.get('t_dur')
    amount_toman = context.user_data.get('t_amt')
    
    try:
        await asyncio.to_thread(create_discount_code, code, 0, amount_toman, max_uses, expires_at, pkg, update.effective_user.id)
        context.user_data.clear()
        await query.edit_message_text(f"کد تخفیف با موفقیت ثبت شد ✅\n\nکد: {code}\nمبلغ: {_format_toman(amount_toman)}\nروی پکیج: {pkg} پخشی\nتعداد استفاده: {max_uses}")
    except Exception:
        await query.answer("این کد قبلاً ثبت شده است.", show_alert=True)

async def on_check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not REQUIRED_CHANNEL:
        await query.answer("نیاز به عضویت نیست.", show_alert=True)
        return
        
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if _is_member(member):
            await query.answer("عضویت تایید شد ✅", show_alert=True)
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user.id,
                text=get_setting("welcome_text", DEFAULT_WELCOME_TEXT),
                reply_markup=_main_menu_keyboard(user.id)
            )
        else:
            await query.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)
    except Exception:
        await query.answer("❌ ربات ادمین کانال نیست یا دسترسی ندارد.", show_alert=True)

# Main entry points setup
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands & Simple Callbacks
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_check_join_callback, pattern=r"^check_join$"))
    app.add_handler(CallbackQueryHandler(ref_actions, pattern=r"^ref_"))
    app.add_handler(CallbackQueryHandler(wallet_charge_init, pattern=r"^wallet_charge$"))
    app.add_handler(CallbackQueryHandler(wallet_paid_callback, pattern=r"^wallet_paid$"))
    app.add_handler(CallbackQueryHandler(wallet_admin_callbacks, pattern=r"^wal_"))
    app.add_handler(CallbackQueryHandler(admin_edits_callback, pattern=r"^edit_"))
    app.add_handler(CallbackQueryHandler(inventory_callback, pattern=r"^pkg_"))
    app.add_handler(CallbackQueryHandler(on_verification_decision, pattern=r"^verif\|"))
    app.add_handler(CallbackQueryHandler(payment_admin_callbacks, pattern=r"^pay\|"))
    app.add_handler(CallbackQueryHandler(on_dest_choice, pattern=r"^dest\|"))
    app.add_handler(CallbackQueryHandler(on_takhfif_package_pick, pattern=r"^takhpkg\|"))
    
    app.add_handler(CallbackQueryHandler(lambda u,c: show_admin_stats(u,c, int(u.callback_query.data.split("|")[1])), pattern=r"^adm_pg\|"))
    app.add_handler(CallbackQueryHandler(admin_user_profile, pattern=r"^adm_usr\|"))
    app.add_handler(CallbackQueryHandler(reserve_slots_custom, pattern=r"^(slot\||pkg\||payw_yes|payw_no)"))
    app.add_handler(CallbackQueryHandler(on_discount_choice, pattern=r"^discount\|"))
    app.add_handler(CallbackQueryHandler(on_res_paid_btn, pattern=r"^res_paid_btn$"))
    
    # Message Handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, central_router))

    logger.info("Bot started and ready for Railway.")
    app.run_polling()

if __name__ == "__main__":
    main()
