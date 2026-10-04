<?php
/**
 * Fragment Shop Bot
 * Telegram Stars & Premium shop — single file, SQLite, Railway-ready.
 *
 * Required env : BOT_TOKEN, ADMIN_ID
 * Optional env : see README.md
 */

error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
date_default_timezone_set('Asia/Tehran');
if (function_exists('mb_internal_encoding')) {
    mb_internal_encoding('UTF-8');
}

const DEF_MIN_TOPUP = 5000;
const DEF_MAX_TOPUP = 50000000;
const MIN_TRANSFER  = 1000;
const FJ_MAX        = 8;
const JOIN_CACHE_TTL = 90;
const RATE_TTL       = 300;
const RATE_STALE_MAX = 10800;
const SP_TTL         = 1800;
const SP_STALE_MAX   = 21600;
const SP_NOTIFY_PCT  = 3;
const RATE_LIVE_TTL  = 10;
const BOOST_MIN_DEF  = 10;
const BOOST_MAX      = 100000;
const FRAGMENT_UA    = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const BRAND = 'RHINO GIFT';
const TEAM  = 'RHINO';

const BTN = [
    'account'  => '👤 حساب کاربری',
    'services' => '{e:cart} خرید و سرویس‌ها',
    'help'     => '🚦 راهنما و قوانین',
    'topup'    => '💰 شارژ حساب',
    'support'  => '👮🏻 پشتیبانی',
    'back'     => '◀️ بازگشت',
];

const ADM = [
    'stats'       => '📊 امار ربات',
    'bc'          => '📨 پیام همگانی',
    'fwd'         => '📨 فوروارد همگانی',
    'svc'         => '🔧 مدیریت سرویس ها',
    'coin_add'    => '💰 افزایش موجودی',
    'coin_sub'    => '💰 کاهش موجودی',
    'check'       => '👀 چک کردن کاربر',
    'msg'         => '📭 ارسال پیام به کاربر',
    'admins'      => '👑 مدیریت ادمین‌ها',
    'force_join'  => '📢 قفل جوین اجباری',
    'gateway'     => '🌐 درگاه پرداخت ریالی',
    'card'        => '💳 تنظیم کارت به کارت',
    'tron'        => '🪙 آدرس ترون',
    'gram'        => '{e:ton} آدرس گرام (TON)',
    'rates'       => '💱 نرخ ارز',
    'stars_price' => '⭐ قیمت استارز',
    'profit'      => '📈 تنظیم سود محصولات',
    'gifts'       => '🎁 قیمت گیفت استارزی',
    'boost'       => '🚀 قیمت بوست',
    'emoji'       => '✨ کانال ایموجی پریمیوم',
    'kyc'         => '🪪 احراز هویت',
    'bot_on'      => '✅ روشن کردن ربات',
    'bot_off'     => '❌ خاموش کردن ربات',
    'ban'         => '❌ بن یوزر',
    'unban'       => '✅ ازاد کردن کاربر',
    'texts'       => '🗂 تنظیمات متن',
    'settings'    => '🤖 تنظیمات ربات',
];

const COINS = [
    'trx' => ['name' => 'ترون (TRX)', 'icon' => '🪙', 'nob' => 'trx', 'short' => 'ترون'],
    'ton' => ['name' => 'گرام (TON)', 'icon' => '{e:ton}', 'nob' => 'ton', 'short' => 'گرام'],
];

const WALLETS = [
    'tron' => [
        'col'   => 'tron_walet',
        'on'    => 'tron',
        'rate'  => 'trx',
        'title' => 'ترون (TRX)',
        'icon'  => '🪙',
        'hint'  => 'آدرس ترون با حرف T شروع می‌شود و ۳۴ کاراکتر است.' . "\n" . 'مثال: <code>TXyz...</code>',
    ],
    'ton' => [
        'col'   => 'tonwalet',
        'on'    => 'ton',
        'rate'  => 'ton',
        'title' => 'گرام (TON)',
        'icon'  => '{e:ton}',
        'hint'  => 'آدرس گرام (TON) معمولا با UQ یا EQ شروع می‌شود و ۴۸ کاراکتر است.' . "\n" . 'مثال: <code>UQ...</code>',
    ],
];

const TOGGLES = [
    'shop' => [
        'title' => '🔌 روش‌های شارژ حساب',
        'items' => [
            'idpay' => 'درگاه ایدی پی',
            'ton'   => 'پرداخت با گرام (TON)',
            'tron'  => 'پرداخت با ترون',
            'cart'  => 'کارت به کارت',
        ],
    ],
    'pay' => [
        'title' => '🧩 تنظیمات فروش',
        'items' => [
            'pay'     => 'افزایش موجودی (کل)',
            'sell'    => 'فروشگاه (کل)',
            'stars'   => 'فروش استارز',
            'permium' => 'فروش پرمیوم',
            'k_gift'  => 'فروش گیفت استارزی',
            'k_boost' => 'فروش بوست کانال و گروه',
            'k_pe'    => 'ایموجی پریمیوم و دکمه‌های رنگی',
        ],
    ],
];

const GIFTS = [
    1  => ['name' => 'قلب صورتی', 'icon' => '💝', 'stars' => 15],
    2  => ['name' => 'تدی', 'icon' => '🧸', 'stars' => 15],
    3  => ['name' => 'باکس کادو', 'icon' => '🎁', 'stars' => 25],
    4  => ['name' => 'گل رز', 'icon' => '🌹', 'stars' => 25],
    5  => ['name' => 'کیک تولد', 'icon' => '🎂', 'stars' => 50],
    6  => ['name' => 'دسته گل', 'icon' => '💐', 'stars' => 50],
    7  => ['name' => 'راکت', 'icon' => '🚀', 'stars' => 50],
    8  => ['name' => 'جام', 'icon' => '🏆', 'stars' => 100],
    9  => ['name' => 'حلقه', 'icon' => '💍', 'stars' => 100],
    10 => ['name' => 'الماس', 'icon' => '{e:g10}', 'stars' => 100],
    11 => ['name' => 'مشروب', 'icon' => '🍾', 'stars' => 50],
];

const BOOSTS = [
    's' => ['name' => 'بوست ۱ الی ۵ روزه تضمینی', 'short' => '۱ الی ۵ روزه', 'number' => 5],
    'l' => ['name' => 'بوست ۳۰ روزه تضمینی', 'short' => '۳۰ روزه', 'number' => 30],
];

const ADMIN_CALLBACKS = [
    'svc_add_org', 'svc_add_sub', 'svc_del_org', 'svc_del_sub', 'delA', 'delF', 'setcat', 'settype',
    'set_start', 'set_help', 'set_rules', 'menu', 'tg', 'Compile', 'notCompile', 'cc', 'reply',
    'adm', 'fj', 'gw', 'cd', 'wl', 'rt', 'sp', 'pm', 'pr_auto', 'pr_manual',
    'gf', 'bp', 'em', 'kya', 'gsel', 'bkind', 'gpr',
];

/* ======================================================================
 *  Helpers
 * ==================================================================== */

function env(string $key, string $default = ''): string
{
    $v = getenv($key);
    if ($v === false || $v === '') {
        $v = $_SERVER[$key] ?? ($_ENV[$key] ?? '');
    }
    $v = trim((string)$v);
    return $v === '' ? $default : $v;
}

function logx(string $msg): void
{
    error_log('[bot] ' . $msg);
}

function h($s): string
{
    return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function money($n): string
{
    return number_format((int)$n);
}

function digits_en(string $s): string
{
    return strtr($s, [
        '۰' => '0', '۱' => '1', '۲' => '2', '۳' => '3', '۴' => '4',
        '۵' => '5', '۶' => '6', '۷' => '7', '۸' => '8', '۹' => '9',
        '٠' => '0', '١' => '1', '٢' => '2', '٣' => '3', '٤' => '4',
        '٥' => '5', '٦' => '6', '٧' => '7', '٨' => '8', '٩' => '9',
    ]);
}

function parse_int(string $s): ?int
{
    $s = digits_en(trim($s));
    $s = str_replace([',', ' ', '٬', '،'], '', $s);
    return preg_match('/^\d{1,12}$/', $s) ? (int)$s : null;
}

function clean_desc(?string $d): string
{
    $d = trim((string)$d);
    return in_array(strtolower($d), ['', '-', 'on', 'none'], true) ? '' : $d;
}

function parse_float(string $s): ?float
{
    $s = digits_en(trim($s));
    $s = str_replace(['٫', '/', ',', '،', ' '], ['.', '.', '.', '.', ''], $s);
    return preg_match('/^\d{1,6}(\.\d{1,4})?$/', $s) ? (float)$s : null;
}

function ago(int $ts): string
{
    if ($ts <= 0) {
        return '—';
    }
    $d = max(0, time() - $ts);
    if ($d < 60) {
        return 'چند ثانیه پیش';
    }
    if ($d < 3600) {
        return intdiv($d, 60) . ' دقیقه پیش';
    }
    if ($d < 86400) {
        return intdiv($d, 3600) . ' ساعت پیش';
    }
    return intdiv($d, 86400) . ' روز پیش';
}

function b64u(string $s): string
{
    return rtrim(strtr(base64_encode($s), '+/', '-_'), '=');
}

function b64u_dec(string $s): string
{
    $r = base64_decode(strtr($s, '-_', '+/'), true);
    return $r === false ? '' : $r;
}

function safe_url(string $u): bool
{
    if (mb_strlen($u) > 400 || !preg_match('~^https://[^\s]+$~i', $u)) {
        return false;
    }
    $host = strtolower((string)parse_url($u, PHP_URL_HOST));
    if ($host === '' || $host === 'localhost' || str_ends_with($host, '.local') || str_ends_with($host, '.internal')) {
        return false;
    }
    if (filter_var($host, FILTER_VALIDATE_IP)
        && !filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
        return false;
    }
    return true;
}

function luhn_ok(string $n): bool
{
    $sum = 0;
    $alt = false;
    for ($i = strlen($n) - 1; $i >= 0; $i--) {
        $d = (int)$n[$i];
        if ($alt) {
            $d *= 2;
            if ($d > 9) {
                $d -= 9;
            }
        }
        $sum += $d;
        $alt = !$alt;
    }
    return $sum % 10 === 0;
}

function b58_decode(string $s): ?string
{
    $alpha = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    $bytes = [];
    $len   = strlen($s);
    for ($i = 0; $i < $len; $i++) {
        $carry = strpos($alpha, $s[$i]);
        if ($carry === false) {
            return null;
        }
        for ($j = count($bytes) - 1; $j >= 0; $j--) {
            $carry += $bytes[$j] * 58;
            $bytes[$j] = $carry & 0xFF;
            $carry >>= 8;
        }
        while ($carry > 0) {
            array_unshift($bytes, $carry & 0xFF);
            $carry >>= 8;
        }
    }
    for ($i = 0; $i < $len && $s[$i] === '1'; $i++) {
        array_unshift($bytes, 0);
    }
    return $bytes ? pack('C*', ...$bytes) : '';
}

function tron_valid(string $a): bool
{
    if (!preg_match('/^T[1-9A-HJ-NP-Za-km-z]{33}$/', $a)) {
        return false;
    }
    $bin = b58_decode($a);
    if ($bin === null || strlen($bin) !== 25 || $bin[0] !== "\x41") {
        return false;
    }
    return substr(hash('sha256', hash('sha256', substr($bin, 0, 21), true), true), 0, 4) === substr($bin, 21);
}

function crc16_xmodem(string $d): int
{
    $crc = 0;
    $n   = strlen($d);
    for ($i = 0; $i < $n; $i++) {
        $crc ^= ord($d[$i]) << 8;
        for ($j = 0; $j < 8; $j++) {
            $crc = ($crc & 0x8000) ? (($crc << 1) ^ 0x1021) : ($crc << 1);
            $crc &= 0xFFFF;
        }
    }
    return $crc;
}

function ton_valid(string $a): bool
{
    if (preg_match('/^-?\d+:[0-9a-fA-F]{64}$/', $a)) {
        return true;
    }
    if (!preg_match('/^[A-Za-z0-9_\-+\/=]{48}$/', $a)) {
        return false;
    }
    $bin = base64_decode(strtr($a, '-_', '+/'), true);
    if ($bin === false || strlen($bin) !== 36) {
        return false;
    }
    $crc = unpack('n', substr($bin, 34, 2))[1];
    return crc16_xmodem(substr($bin, 0, 34)) === $crc;
}

/* ======================================================================
 *  Jalali date
 * ==================================================================== */

final class Jalali
{
    public static function fromGregorian(int $gy, int $gm, int $gd): array
    {
        $gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        if ($gy > 1600) {
            $jy = 979;
            $gy -= 1600;
        } else {
            $jy = 0;
            $gy -= 621;
        }
        $gy2  = ($gm > 2) ? ($gy + 1) : $gy;
        $days = (365 * $gy) + intdiv($gy2 + 3, 4) - intdiv($gy2 + 99, 100) + intdiv($gy2 + 399, 400) - 80 + $gd + $gdm[$gm - 1];
        $jy  += 33 * intdiv($days, 12053);
        $days %= 12053;
        $jy  += 4 * intdiv($days, 1461);
        $days %= 1461;
        $jy  += intdiv($days - 1, 365);
        if ($days > 365) {
            $days = ($days - 1) % 365;
        }
        if ($days < 186) {
            $jm = 1 + intdiv($days, 31);
            $jd = 1 + ($days % 31);
        } else {
            $jm = 7 + intdiv($days - 186, 30);
            $jd = 1 + (($days - 186) % 30);
        }
        return [$jy, $jm, $jd];
    }

    private static function now(?int $ts): DateTime
    {
        $dt = new DateTime('@' . ($ts ?? time()));
        $dt->setTimezone(new DateTimeZone('Asia/Tehran'));
        return $dt;
    }

    public static function date(?int $ts = null): string
    {
        $dt = self::now($ts);
        [$y, $m, $d] = self::fromGregorian((int)$dt->format('Y'), (int)$dt->format('n'), (int)$dt->format('j'));
        return sprintf('%04d/%02d/%02d', $y, $m, $d);
    }

    public static function time(?int $ts = null): string
    {
        return self::now($ts)->format('H:i:s');
    }
}

/* ======================================================================
 *  Config
 * ==================================================================== */

final class Config
{
    public static string $token = '';
    public static array $admins = [];
    public static string $dbPath = '';
    public static string $dataDir = '';

    public static function load(): void
    {
        self::$token = env('BOT_TOKEN');

        $ids = preg_split('/[\s,;]+/', env('ADMIN_ID')) ?: [];
        foreach ($ids as $id) {
            if (ctype_digit($id) && (int)$id > 0) {
                self::$admins[] = (int)$id;
            }
        }

        $path = env('SQLITE_PATH');
        if ($path === '') {
            $vol = env('RAILWAY_VOLUME_MOUNT_PATH');
            if ($vol !== '') {
                $dir = $vol;
            } elseif (is_dir('/data') && is_writable('/data')) {
                $dir = '/data';
            } else {
                $dir = __DIR__ . '/data';
            }
            $path = rtrim($dir, '/\\') . '/bot.db';
        }
        self::$dbPath  = $path;
        self::$dataDir = dirname($path);
        if (!is_dir(self::$dataDir)) {
            @mkdir(self::$dataDir, 0775, true);
        }
    }
}

/* ======================================================================
 *  Database (SQLite)
 * ==================================================================== */

final class Db
{
    private static ?PDO $pdo = null;
    private static ?array $setting = null;
    private static ?array $texts = null;

    private const SCHEMA = "
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INTEGER PRIMARY KEY,
            `step` TEXT,
            `time` TEXT,
            `number` TEXT,
            `coin` TEXT,
            `account` TEXT,
            `date` TEXT
        );
        CREATE TABLE IF NOT EXISTS `setting` (
            `bot` TEXT,
            `ton` TEXT,
            `stars` TEXT,
            `permium` TEXT,
            `tron` TEXT,
            `pay` TEXT,
            `idpay` TEXT,
            `cart` TEXT,
            `sell` TEXT,
            `tron_walet` TEXT,
            `idpay_merchant` TEXT,
            `cart_number` TEXT,
            `Percentage` TEXT,
            `Percentage_result` TEXT,
            `tonwalet` TEXT,
            `fragment` TEXT
        );
        CREATE TABLE IF NOT EXISTS `ProductsA` (
            `id` INTEGER PRIMARY KEY,
            `name` TEXT,
            `Description` TEXT,
            `time` TEXT,
            `date` TEXT
        );
        CREATE TABLE IF NOT EXISTS `ProductsF` (
            `id` INTEGER PRIMARY KEY,
            `name` TEXT,
            `Description` TEXT,
            `time` TEXT,
            `date` TEXT,
            `price` TEXT,
            `ProductsA` TEXT,
            `Fragment` TEXT,
            `number` TEXT,
            `startsorpermium` TEXT
        );
        CREATE TABLE IF NOT EXISTS `Orders` (
            `id` TEXT,
            `products_id` TEXT,
            `user` TEXT,
            `user_id` TEXT,
            `time` TEXT,
            `date` TEXT,
            `price` TEXT,
            `result` TEXT
        );
        CREATE TABLE IF NOT EXISTS `texts` (
            `help` TEXT,
            `ruls` TEXT,
            `start` TEXT
        );
        CREATE TABLE IF NOT EXISTS `code` (
            `code` TEXT,
            `users` TEXT,
            `result` TEXT,
            `time` TEXT,
            `coin` TEXT
        );
        CREATE TABLE IF NOT EXISTS `trons_pay` (
            `id` TEXT,
            `user` TEXT,
            `tron` TEXT,
            `price_toman` TEXT,
            `walet` TEXT,
            `time` TEXT,
            `date` TEXT,
            `result` TEXT
        );
        CREATE TABLE IF NOT EXISTS `tron_pays` (
            `id` TEXT,
            `user` TEXT,
            `tron` TEXT,
            `hash` TEXT,
            `time` TEXT,
            `date` TEXT,
            `result` TEXT
        );
        CREATE TABLE IF NOT EXISTS `ton_pays` (
            `id` TEXT,
            `user` TEXT,
            `tron` TEXT,
            `hash` TEXT,
            `time` TEXT,
            `date` TEXT,
            `result` TEXT
        );
        CREATE TABLE IF NOT EXISTS `admin` (
            `id` TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_orders_id ON `Orders` (`id`);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON `Orders` (`user`);
        CREATE INDEX IF NOT EXISTS idx_productsf_cat ON `ProductsF` (`ProductsA`);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ton_hash ON `ton_pays` (`hash`);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_tron_hash ON `tron_pays` (`hash`);
    ";

    private const SCHEMA_V2 = "
        CREATE TABLE IF NOT EXISTS `kv` (
            `k` TEXT PRIMARY KEY,
            `v` TEXT
        );
        CREATE TABLE IF NOT EXISTS `joincache` (
            `uid` INTEGER,
            `ch` TEXT,
            `ts` INTEGER,
            PRIMARY KEY (`uid`, `ch`)
        );
    ";

    private const SCHEMA_V3 = "
        CREATE TABLE IF NOT EXISTS `kyc` (
            `uid` INTEGER PRIMARY KEY,
            `status` TEXT,
            `card` TEXT,
            `reason` TEXT,
            `file_id` TEXT,
            `ftype` TEXT,
            `name` TEXT,
            `username` TEXT,
            `ts` INTEGER,
            `upd` INTEGER
        );
    ";

    private const VERSION = 3;

    private static ?array $kv = null;

    public static function pdo(): PDO
    {
        if (self::$pdo instanceof PDO) {
            return self::$pdo;
        }
        $pdo = new PDO('sqlite:' . Config::$dbPath, null, null, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
            PDO::ATTR_TIMEOUT            => 10,
        ]);
        $pdo->exec('PRAGMA busy_timeout = 10000');
        $pdo->exec('PRAGMA journal_mode = WAL');
        $pdo->exec('PRAGMA synchronous = NORMAL');
        $pdo->exec('PRAGMA foreign_keys = ON');
        self::$pdo = $pdo;
        self::init($pdo);
        return $pdo;
    }

    private static function init(PDO $pdo): void
    {
        if ((int)$pdo->query('PRAGMA user_version')->fetchColumn() >= self::VERSION) {
            return;
        }
        $pdo->exec('BEGIN IMMEDIATE');
        try {
            $ver = (int)$pdo->query('PRAGMA user_version')->fetchColumn();
            if ($ver < self::VERSION) {
                $pdo->exec(self::SCHEMA);
                $pdo->exec(self::SCHEMA_V2);
                $pdo->exec(self::SCHEMA_V3);

                if ((int)$pdo->query('SELECT COUNT(*) FROM `setting`')->fetchColumn() === 0) {
                    $st = $pdo->prepare('INSERT INTO `setting`
                        (`bot`,`ton`,`stars`,`permium`,`tron`,`pay`,`idpay`,`cart`,`sell`,`tron_walet`,`idpay_merchant`,`cart_number`,`Percentage`,`Percentage_result`,`tonwalet`,`fragment`)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
                    $st->execute([
                        'on', 'on', 'on', 'on', 'on', 'on', 'on', 'on', 'on',
                        '', '', '',
                        '0', '0', '', '',
                    ]);
                }

                if ((int)$pdo->query('SELECT COUNT(*) FROM `texts`')->fetchColumn() === 0) {
                    $st = $pdo->prepare('INSERT INTO `texts` (`help`,`ruls`,`start`) VALUES (?,?,?)');
                    $st->execute([
                        "📖 <b>راهنمای خرید</b>\n\n🔹 از بخش «افزایش موجودی» حساب خود را شارژ کنید.\n🔹 از بخش «سرویس ها» محصول مورد نظر را انتخاب کنید.\n🔹 یوزرنیم اکانت تلگرام گیرنده را ارسال کنید.\n🔹 پس از تایید ادمین، سفارش شما تحویل داده می‌شود.",
                        "📜 <b>قوانین</b>\n\n• مسئولیت صحت یوزرنیم واردشده با خریدار است.\n• پس از تحویل سفارش، مبلغ قابل بازگشت نیست.\n• در صورت رد سفارش توسط ادمین، مبلغ به موجودی شما برمی‌گردد.\n• هرگونه سوءاستفاده منجر به مسدود شدن حساب می‌شود.",
                        "👋 سلام! به فروشگاه <b>استارز و پرمیوم تلگرام</b> خوش آمدید.\n\n⭐ خرید سریع و مطمئن استارز\n👑 خرید اشتراک تلگرام پرمیوم\n\nبرای شروع از منوی زیر استفاده کنید 👇",
                    ]);
                }
                $pdo->exec('PRAGMA user_version = ' . self::VERSION);
            }
            $pdo->exec('COMMIT');
        } catch (Throwable $e) {
            try {
                $pdo->exec('ROLLBACK');
            } catch (Throwable $ignored) {
            }
            throw $e;
        }
    }

    public static function q(string $sql, array $p = []): PDOStatement
    {
        $st = self::pdo()->prepare($sql);
        $st->execute($p);
        return $st;
    }

    public static function row(string $sql, array $p = []): ?array
    {
        $r = self::q($sql, $p)->fetch();
        return $r === false ? null : $r;
    }

    public static function rows(string $sql, array $p = []): array
    {
        return self::q($sql, $p)->fetchAll();
    }

    public static function col(string $sql, array $p = []): array
    {
        return self::q($sql, $p)->fetchAll(PDO::FETCH_COLUMN);
    }

    public static function val(string $sql, array $p = [])
    {
        $r = self::q($sql, $p)->fetchColumn();
        return $r === false ? null : $r;
    }

    public static function exec(string $sql, array $p = []): int
    {
        return self::q($sql, $p)->rowCount();
    }

    public static function tx(callable $fn)
    {
        $pdo = self::pdo();
        $pdo->exec('BEGIN IMMEDIATE');
        try {
            $r = $fn();
            $pdo->exec('COMMIT');
            return $r;
        } catch (Throwable $e) {
            try {
                $pdo->exec('ROLLBACK');
            } catch (Throwable $ignored) {
            }
            throw $e;
        }
    }

    public static function setting(): array
    {
        if (self::$setting === null) {
            self::$setting = self::row('SELECT * FROM `setting` LIMIT 1') ?? [];
        }
        return self::$setting;
    }

    public static function setSetting(string $col, string $val): void
    {
        $allowed = ['bot', 'ton', 'stars', 'permium', 'tron', 'pay', 'idpay', 'cart', 'sell',
            'tron_walet', 'idpay_merchant', 'cart_number', 'tonwalet'];
        if (!in_array($col, $allowed, true)) {
            return;
        }
        self::exec("UPDATE `setting` SET `$col` = ?", [$val]);
        self::$setting = null;
    }

    public static function kv(string $k, string $default = ''): string
    {
        if (self::$kv === null) {
            self::$kv = [];
            foreach (self::rows('SELECT k, v FROM kv') as $r) {
                self::$kv[(string)$r['k']] = (string)$r['v'];
            }
        }
        return self::$kv[$k] ?? $default;
    }

    public static function kvSet(string $k, string $v): void
    {
        self::kv('');
        self::exec('INSERT INTO kv (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v', [$k, $v]);
        self::$kv[$k] = $v;
    }

    public static function texts(): array
    {
        if (self::$texts === null) {
            self::$texts = self::row('SELECT * FROM `texts` LIMIT 1') ?? [];
        }
        return self::$texts;
    }

    public static function setText(string $col, string $val): void
    {
        if (!in_array($col, ['help', 'ruls', 'start'], true)) {
            return;
        }
        self::exec("UPDATE `texts` SET `$col` = ?", [$val]);
        self::$texts = null;
    }
}

/* ======================================================================
 *  Users / balance / admins
 * ==================================================================== */

function user_get(int $id): array
{
    $u = Db::row('SELECT * FROM users WHERE id = ?', [$id]);
    if (!$u) {
        Db::exec(
            'INSERT OR IGNORE INTO users (id, step, time, number, coin, account, date) VALUES (?,?,?,?,?,?,?)',
            [$id, 'none', Jalali::time(), '0', '0', 'none', Jalali::date()]
        );
        $u = Db::row('SELECT * FROM users WHERE id = ?', [$id]);
    }
    return $u ?? ['id' => $id, 'step' => 'none', 'coin' => '0', 'account' => 'none', 'number' => '0', 'time' => '', 'date' => ''];
}

function user_exists(int $id): bool
{
    return Db::val('SELECT 1 FROM users WHERE id = ?', [$id]) !== null;
}

function set_step(int $id, string $step): void
{
    Db::exec('UPDATE users SET step = ? WHERE id = ?', [$step, $id]);
}

function coin_add(int $id, int $amount): void
{
    Db::exec('UPDATE users SET coin = CAST(coin AS INTEGER) + CAST(? AS INTEGER) WHERE id = ?', [$amount, $id]);
}

function coin_sub(int $id, int $amount): bool
{
    return Db::exec(
        'UPDATE users SET coin = CAST(coin AS INTEGER) - CAST(? AS INTEGER)
         WHERE id = ? AND CAST(coin AS INTEGER) >= CAST(? AS INTEGER)',
        [$amount, $id, $amount]
    ) > 0;
}

function coin_of(int $id): int
{
    return (int)Db::val('SELECT CAST(coin AS INTEGER) FROM users WHERE id = ?', [$id]);
}

function all_admins(): array
{
    $ids = Config::$admins;
    foreach (Db::col('SELECT id FROM admin') as $a) {
        if (ctype_digit((string)$a)) {
            $ids[] = (int)$a;
        }
    }
    return array_values(array_unique($ids));
}

function is_admin(int $id): bool
{
    return in_array($id, all_admins(), true);
}

function notify_admins(string $text, ?array $markup = null): void
{
    foreach (all_admins() as $a) {
        Tg::send($a, $text, $markup);
    }
}

/* ======================================================================
 *  Telegram client
 * ==================================================================== */

/* ======================================================================
 *  Premium emoji + coloured buttons (applied centrally in Tg::call)
 *
 *  - every emoji in message text/captions becomes <tg-emoji> when we own an id for it
 *  - first emoji (or {e:name} token) of a button label becomes its icon_custom_emoji_id
 *  - every button gets a style (primary / success / danger)
 *  Needs the bot OWNER to have Telegram Premium. If Telegram refuses, we
 *  transparently fall back to plain emoji (and keep colours when possible).
 * ==================================================================== */

final class Pe
{
    public const NAMED = [
        'stars'   => ['5785084140395172124', '⭐'],
        'premium' => ['5978986632315931621', '👑'],
        'boost'   => ['5895735846698487922', '🚀'],
        'ton'     => ['6030549140633555631', '💎'],
        'trx'     => ['6028143164378845862', '🪙'],
        'usd'     => ['6034851808805918335', '💵'],
        'cart'    => ['5312361253610475399', '🛒'],
        'bag'     => ['5780824606579364273', '🛍'],
        'bolt'    => ['5400366091283229916', '⚡'],
        'gem'     => ['5913763237484043685', '💎'],
        'g1'      => ['6028404508843842802', '💝'],
        'g2'      => ['5206502842478638898', '🧸'],
        'g3'      => ['5327976616532412608', '🎁'],
        'g4'      => ['5363938656874673963', '🌹'],
        'g5'      => ['5780406568822511615', '🎂'],
        'g6'      => ['5363938656874673963', '💐'],
        'g7'      => ['5895720492190404869', '🚀'],
        'g8'      => ['5440539497383087970', '🏆'],
        'g9'      => ['5427168083074628963', '💍'],
        'g10'     => ['5769454896138949400', '💎'],
        'g11'     => ['6028192874330328851', '🍾'],
    ];

    private const IDS = <<<'MAP'
✅=5915511508216848100
✔=5206607081334906820
❌ ✖=5913246458429054677
⛔ 🚫=5260293700088511294
➕=5916040218690986024
➖ 🔻=5972223227055836399
❗ ‼ ⁉=5792135656356454093
❓ ❔=5436113877181941026
ℹ=5334544901428229844
🛡 🔰=5915760637794854235
👤 👥=5924571861986844013
💻 🖥=5282843764451195532
📝=5924798992742359487
✏ ✍=5395444784611480792
🔖 📛=5222444124698853913
💳=5920122954473021482
💎=5913763237484043685
👮=5911426874059267908
⚠=5906602521979265269
⚙ 🔧 🧩 🔌 🧪=5194980871152623004
🤖 🧠=5895617412975299964
💰=5224257782013769471
📅=5472026645659401564
🗓 📆=5413879192267805083
📋 📖 📜 📄 🧾=5274055917766202507
🛒=5312361253610475399
🛍 📦=5780824606579364273
🗂 📂=5229064374403998351
⭐ 🌟=5785084140395172124
👑=5978986632315931621
🚀=5895720492190404869
🎁=5327976616532412608
💝 ❤=6028404508843842802
🧸=5206502842478638898
🌹 💐=5363938656874673963
🎂=5780406568822511615
🏆 🥇=5440539497383087970
🥈=5447203607294265305
🥉=5453902265922376865
💍=5427168083074628963
🍾=6028192874330328851
🪙=6028143164378845862
💵=6034851808805918335
💱=5402186569006210455
💸=5233326571099534068
📈=5244837092042750681
📉=5246762912428603768
📊 🔢=5231200819986047254
🏠=5416041192905265756
🟢=5416081784641168838
🔴=5411225014148014586
🟡=5852626860516577393
◀ ⬅ ↩ ➡ ▶=5416117059207572332
🆔 🪪=5841276284155467413
🗑=5445267414562389170
⏳ ⌛ ⏱=5386367538735104399
🔗=5271604874419647061
🌐=5447410659077661506
🔄=5375338737028841420
📌=5397782960512444700
🎯 📍=5391032818111363540
📢 📣=5424818078833715060
✨ ✳=5325547803936572038
📩 📨 📬 📭 ✉=5253742260054409879
⚡=5400366091283229916
🔍 🔎=5231012545799666522
⚪=5978703138704591679
🔹 🔸=5971910695170609186
👈=5971910695170609186
👇 ☝ 👆=5019759554234156094
👀=5210956306952758910
👋 🎉=5461151367559141950
😍 🤩 🙏 🫶=5895341521456073725
🔒=5296369303661067030
🔑 🔐=5897604269141398480
⬇ 🔽=5447183459602669338
⬆ 🔼=5449683594425410231
🏦 🏪=5895288113537748673
👨‍💻=5897785405092138893
🚦 🚨=5395695537687123235
🔔 🛎=5458603043203327669
☎ 📲 📞=5895468772747120404
👛 👜=5296387887984580731
🆕=5382357040008021292
💡=5422439311196834318
💯=5341498088408234504
🎥 📷=5895731156594200261
💬 💭=5443038326535759644
🔥=5424972470023104089
🙂=5461117441612462242
👍=5337080053119336309
👎=5449875686837726134
🆓=5406756500108501710
🆒=5222079954421818267
🔈 🎵=5388632425314140043
MAP;

    public const EMOJI_BODY = '(?:[\x{1F1E6}-\x{1F1FF}]{2}|[0-9#*]\x{FE0F}?\x{20E3}|\p{Extended_Pictographic}[\x{FE0F}\x{1F3FB}-\x{1F3FF}]?(?:\x{200D}\p{Extended_Pictographic}[\x{FE0F}\x{1F3FB}-\x{1F3FF}]?)*)';
    public const EMOJI_RE   = '/' . self::EMOJI_BODY . '/u';

    private static ?array $map = null;
    public static bool $used   = false;
    public static bool $styled = false;

    public static function key(string $e): string
    {
        return (string)preg_replace('/[\x{FE0F}\x{1F3FB}-\x{1F3FF}]/u', '', $e);
    }

    public static function id(string $e): ?string
    {
        if (self::$map === null) {
            self::$map = [];
            foreach (explode("\n", self::IDS) as $line) {
                $line = trim($line);
                if ($line === '' || !str_contains($line, '=')) {
                    continue;
                }
                [$chars, $id] = explode('=', $line, 2);
                foreach (preg_split('/\s+/u', trim($chars)) as $c) {
                    if ($c !== '') {
                        self::$map[self::key($c)] = $id;
                    }
                }
            }
        }
        return self::$map[self::key($e)] ?? null;
    }

    public static function label(string $s): string
    {
        $s = (string)preg_replace('/\{e:\w+\}/u', '', $s);
        $s = (string)preg_replace(self::EMOJI_RE, '', $s);
        return trim((string)preg_replace('/[ \t\x{00A0}]+/u', ' ', $s));
    }

    public static function strip(string $s): string
    {
        $s = (string)preg_replace('/\{e:\w+\}/u', '', $s);
        $s = (string)preg_replace(self::EMOJI_RE, '', $s);
        return trim((string)preg_replace('/[ \t\x{00A0}]{2,}/u', ' ', $s));
    }

    public static function mode(): int
    {
        if (Db::kv('k_pe', 'on') !== 'on') {
            return 1;
        }
        return (int)Db::kv('pe_block', '0') > time() ? 1 : 0;
    }

    public static function html(string $t, int $mode): string
    {
        $parts = preg_split('~(<(?:code|pre)\b[^>]*>.*?</(?:code|pre)>|<[^>]*>)~isu', $t, -1, PREG_SPLIT_DELIM_CAPTURE);
        if ($parts === false) {
            return $t;
        }
        foreach ($parts as $i => $seg) {
            if ($i % 2 === 1 || $seg === '') {
                continue;
            }
            if ($mode === 0) {
                $seg = (string)preg_replace_callback(self::EMOJI_RE, function ($m) {
                    $id = self::id($m[0]);
                    if ($id === null) {
                        return $m[0];
                    }
                    self::$used = true;
                    return '<tg-emoji emoji-id="' . $id . '">' . $m[0] . '</tg-emoji>';
                }, $seg);
            }
            $seg = (string)preg_replace_callback('/\{e:(\w+)\}/u', function ($m) use ($mode) {
                $n = self::NAMED[$m[1]] ?? null;
                if (!$n) {
                    return '';
                }
                if ($mode > 0) {
                    return $n[1];
                }
                self::$used = true;
                return '<tg-emoji emoji-id="' . $n[0] . '">' . $n[1] . '</tg-emoji>';
            }, $seg);
            $parts[$i] = $seg;
        }
        return implode('', $parts);
    }

    private static function classify(string $first, string $data): string
    {
        $c = explode(',', $data, 3);
        $cmd = $c[0] ?? '';
        $rest = [$c[1] ?? '', $c[2] ?? ''];
        if (in_array($cmd, ['notCompile', 'delA', 'delF', 'svc_del_org', 'svc_del_sub'], true)
            || array_intersect(['no', 'del', 'rev', 'off', 'reset'], $rest)) {
            return 'danger';
        }
        if (in_array($cmd, ['Compile', 'ok', 'joined', 'pr_auto'], true)
            || array_intersect(['ok', 'use', 'mk', 'start'], $rest)) {
            return 'success';
        }
        $k = self::key($first);
        if (in_array($k, ['❌', '🗑', '⛔', '✖', '🔴', '🚫'], true)) {
            return 'danger';
        }
        if (in_array($k, ['✅', '✔', '🟢'], true)) {
            return 'success';
        }
        return 'primary';
    }

    public static function btn($b, int $mode): array
    {
        if (!is_array($b)) {
            $b = ['text' => (string)$b];
        }
        $text = (string)($b['text'] ?? '');
        $icon = null;
        $fb   = '';
        if (preg_match('/^\s*\{e:(\w+)\}\s*/u', $text, $m) && isset(self::NAMED[$m[1]])) {
            [$icon, $fb] = self::NAMED[$m[1]];
            $text = substr($text, strlen($m[0]));
        } elseif (preg_match('/^\s*(' . self::EMOJI_BODY . ')\s*/u', $text, $m)) {
            $fb   = $m[1];
            $icon = self::id($fb);
            $text = substr($text, strlen($m[0]));
        }
        $first = $fb;
        $text  = (string)preg_replace('/\{e:\w+\}/u', '', $text);
        $text  = str_replace(['⭐️', '⭐'], ' استارز', $text);
        $text  = (string)preg_replace(self::EMOJI_RE, '', $text);
        $text  = trim((string)preg_replace('/[ \t\x{00A0}]{2,}/u', ' ', $text));
        if ($text === '') {
            $text = $fb !== '' ? $fb : '•';
            $icon = null;
        }
        if ($icon !== null && $mode === 0) {
            $b['icon_custom_emoji_id'] = $icon;
            self::$used = true;
        } elseif ($fb !== '' && $text !== $fb) {
            $text = $fb . ' ' . $text;
        }
        $b['text'] = $text;
        if ($mode < 2 && !isset($b['style'])) {
            $b['style'] = self::classify($first, (string)($b['callback_data'] ?? ''));
            self::$styled = true;
        }
        return $b;
    }

    public static function markup(array $rm, int $mode): array
    {
        foreach (['inline_keyboard', 'keyboard'] as $k) {
            if (!isset($rm[$k]) || !is_array($rm[$k])) {
                continue;
            }
            foreach ($rm[$k] as $i => $row) {
                foreach ($row as $j => $b) {
                    $rm[$k][$i][$j] = self::btn($b, $mode);
                }
            }
        }
        return $rm;
    }

    public static function prepare(string $method, array $p, int $mode): array
    {
        foreach (['text', 'caption'] as $k) {
            if (!isset($p[$k]) || !is_string($p[$k]) || $method === 'answerCallbackQuery') {
                continue;
            }
            $p[$k] = ($p['parse_mode'] ?? '') === 'HTML'
                ? self::html($p[$k], $mode)
                : (string)preg_replace_callback('/\{e:(\w+)\}/u', fn($m) => self::NAMED[$m[1]][1] ?? '', $p[$k]);
        }
        if ($method === 'answerCallbackQuery' && isset($p['text'])) {
            $p['text'] = self::strip((string)$p['text']);
            if ($p['text'] === '') {
                unset($p['text'], $p['show_alert']);
            }
        }
        if (isset($p['reply_markup']) && is_array($p['reply_markup'])) {
            $p['reply_markup'] = self::markup($p['reply_markup'], $mode);
        }
        return $p;
    }

    public static function looksLikeEmojiError(?array $r): bool
    {
        if (!$r || !empty($r['ok'])) {
            return false;
        }
        $d = strtolower((string)($r['description'] ?? ''));
        foreach (['emoji', 'icon', 'style', 'premium', 'entit', 'document_invalid', 'button_'] as $w) {
            if ($d !== '' && str_contains($d, $w)) {
                return true;
            }
        }
        return false;
    }

    public static function block(): void
    {
        Db::kvSet('pe_block', (string)(time() + 900));
        if (time() - (int)Db::kv('pe_notice', '0') > 21600) {
            Db::kvSet('pe_notice', (string)time());
            notify_admins("⚠️ <b>ایموجی پریمیوم فعال نشد</b>\n\nتلگرام اجازه استفاده از ایموجی پریمیوم را به ربات نداد.\nبرای فعال شدن، اکانتی که ربات را در BotFather ساخته (مالک ربات) باید <b>Telegram Premium</b> داشته باشد.\n\nتا آن زمان ربات با ایموجی معمولی کار می‌کند و هر ۱۵ دقیقه دوباره تلاش می‌کند.");
        }
    }
}

final class Tg
{
    public static function call(string $method, array $params = [], int $timeout = 25): ?array
    {
        $mode = Pe::mode();
        Pe::$used = Pe::$styled = false;
        $res = self::raw($method, Pe::prepare($method, $params, $mode), $timeout);
        $first = $mode;
        while ($mode < 2 && Pe::looksLikeEmojiError($res) && (Pe::$used || Pe::$styled)) {
            $mode++;
            Pe::$used = Pe::$styled = false;
            $res = self::raw($method, Pe::prepare($method, $params, $mode), $timeout);
            if ($first === 0 && $res && !empty($res['ok'])) {
                Pe::block();
            }
        }
        return $res;
    }

    private static function raw(string $method, array $params = [], int $timeout = 25): ?array
    {
        $ch = curl_init('https://api.telegram.org/bot' . Config::$token . '/' . $method);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => json_encode($params ?: new stdClass(), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_TIMEOUT        => $timeout,
        ]);
        $raw = curl_exec($ch);
        if ($raw === false) {
            logx("telegram $method curl error: " . curl_error($ch));
            curl_close($ch);
            return null;
        }
        curl_close($ch);
        $res = json_decode((string)$raw, true);
        if (!is_array($res)) {
            return null;
        }
        if (empty($res['ok'])) {
            $d = (string)($res['description'] ?? '');
            if (!str_contains($d, 'blocked') && !str_contains($d, 'not modified') && !str_contains($d, 'deactivated')) {
                logx("telegram $method failed: $d");
            }
        }
        return $res;
    }

    private static function cut(string $t): string
    {
        return mb_strlen($t) > 4090 ? mb_substr($t, 0, 4090) : $t;
    }

    public static function send($chat, string $text, ?array $markup = null, array $extra = []): ?array
    {
        $p = [
            'chat_id'              => $chat,
            'text'                 => self::cut($text),
            'parse_mode'           => 'HTML',
            'link_preview_options' => ['is_disabled' => true],
        ] + $extra;
        if ($markup !== null) {
            $p['reply_markup'] = $markup;
        }
        $r = self::call('sendMessage', $p);
        if ($r && empty($r['ok']) && str_contains((string)($r['description'] ?? ''), "can't parse entities")) {
            unset($p['parse_mode']);
            $r = self::call('sendMessage', $p);
        }
        return ($r && !empty($r['ok'])) ? $r['result'] : null;
    }

    public static function edit($chat, int $mid, string $text, ?array $markup = null): bool
    {
        $p = [
            'chat_id'              => $chat,
            'message_id'           => $mid,
            'text'                 => self::cut($text),
            'parse_mode'           => 'HTML',
            'link_preview_options' => ['is_disabled' => true],
        ];
        if ($markup !== null) {
            $p['reply_markup'] = $markup;
        }
        $r = self::call('editMessageText', $p);
        if ($r && !empty($r['ok'])) {
            return true;
        }
        return $r && str_contains((string)($r['description'] ?? ''), 'not modified');
    }

    public static function answer(string $id, string $text = '', bool $alert = false): void
    {
        $p = ['callback_query_id' => $id];
        if ($text !== '') {
            $p['text']       = $text;
            $p['show_alert'] = $alert;
        }
        self::call('answerCallbackQuery', $p, 10);
    }

    public static function delete($chat, int $mid): void
    {
        self::call('deleteMessage', ['chat_id' => $chat, 'message_id' => $mid], 10);
    }
}

/* ======================================================================
 *  Keyboards / UI helpers
 * ==================================================================== */

function ik(array $rows): array
{
    return ['inline_keyboard' => $rows];
}

function cb(string $text, string $data): array
{
    return ['text' => $text, 'callback_data' => $data];
}

function ub(string $text, string $url): array
{
    return ['text' => $text, 'url' => $url];
}

function rk(array $rows): array
{
    return ['keyboard' => $rows, 'resize_keyboard' => true];
}

function kb_back(): array
{
    return rk([[BTN['back']]]);
}

function kb_panel(): array
{
    return rk([
        [ADM['stats']],
        [ADM['bc'], ADM['fwd']],
        [ADM['svc']],
        [ADM['coin_add'], ADM['coin_sub']],
        [ADM['check'], ADM['msg']],
        [ADM['admins'], ADM['force_join']],
        [ADM['gateway'], ADM['card']],
        [ADM['tron'], ADM['gram']],
        [ADM['rates'], ADM['stars_price']],
        [ADM['profit']],
        [ADM['gifts'], ADM['boost']],
        [ADM['emoji'], ADM['kyc']],
        [ADM['bot_on'], ADM['bot_off']],
        [ADM['ban'], ADM['unban']],
        [ADM['texts'], ADM['settings']],
        [BTN['back']],
    ]);
}

function kb_main(): array
{
    return ik([
        [cb(BTN['account'], 'account'), cb(BTN['services'], 'my_bots')],
        [cb(BTN['help'], 'help'), cb(BTN['topup'], 'add_coin')],
        [cb(BTN['support'], 'support')],
    ]);
}

function screen(int $chat, int $mid, string $text, ?array $markup = null): void
{
    if ($mid > 0 && Tg::edit($chat, $mid, $text, $markup)) {
        return;
    }
    Tg::send($chat, $text, $markup);
}

function drop_reply_kb(int $chat): void
{
    $m = Tg::send($chat, '⏳', ['remove_keyboard' => true]);
    if ($m && isset($m['message_id'])) {
        Tg::delete($chat, (int)$m['message_id']);
    }
}

const HR = '━━━━━━━━━━━━━━━━━━';

function head(string $icon, string $title): string
{
    return $icon . ' <b>' . $title . "</b>\n" . HR . "\n\n";
}

function txt_custom(string $col): bool
{
    return Db::kv('txt_custom_' . $col, '') === '1';
}

function txt_get(string $col): string
{
    if (txt_custom($col)) {
        $t = clean_desc(Db::texts()[$col] ?? '');
        if ($t !== '') {
            return $t;
        }
    }
    return match ($col) {
        'start' => default_start(),
        'help'  => default_help(),
        'ruls'  => default_rules(),
        default => '',
    };
}

function default_start(): string
{
    return head('✨', BRAND)
        . "سلام رفیق، خوش اومدی به فروشگاه تیم <b>" . TEAM . "</b> 🎉\n\n"
        . "{e:stars} استارز تلگرام\n"
        . "{e:premium} اشتراک پریمیوم\n"
        . "🎁 گیفت‌های استارزی\n"
        . "{e:boost} بوست کانال و گروه\n\n"
        . "🔹 قیمت‌ها لحظه‌ای و منصفانه\n"
        . "🔹 خرید سریع، امن و بدون دردسر\n"
        . "🔹 پشتیبانی همیشه کنارته\n\n"
        . "👇 از دکمه‌های زیر شروع کن";
}

function default_help(): string
{
    return head('📖', 'راهنمای کامل ' . BRAND)
        . '<b>' . BRAND . "</b> فروشگاه رسمی تیم <b>" . TEAM . "</b> برای خرید امن و سریع خدمات تلگرامه؛ همه‌چیز از همین ربات انجام می‌شه، بدون واسطه و بدون دردسر ✨\n\n"
        . "{e:cart} <b>محصولات و خدمات ما</b>\n\n"
        . "{e:stars} <b>استارز تلگرام</b>\nهر تعداد استارز که بخوای، مستقیم روی اکانتی که خودت مشخص می‌کنی. قیمت‌ها بر اساس نرخ لحظه‌ای بازار محاسبه می‌شن.\n\n"
        . "{e:premium} <b>اشتراک پریمیوم</b>\nاشتراک رسمی Telegram Premium برای ۳، ۶ یا ۱۲ ماه، بدون نیاز به ورود به اکانتت؛ فقط یوزرنیم کافیه.\n\n"
        . "🎁 <b>گیفت استارزی</b>\nگیفت‌های اختصاصی مثل تدی، گل رز، کیک تولد، قلب، الماس و ... که مستقیم برای گیرنده ارسال می‌شن؛ مناسب هدیه دادن به عزیزانت.\n\n"
        . "{e:boost} <b>بوست کانال و گروه</b>\nبوست «۱ الی ۵ روزه تضمینی» و «۳۰ روزه تضمینی» برای بالا بردن لول کانال یا گروه (حداقل سفارش " . boost_min() . " بوست).\n\n"
        . HR . "\n\n"
        . "🎯 <b>مراحل خرید، قدم‌به‌قدم</b>\n\n"
        . "🔹 <b>۱. شارژ حساب:</b> از دکمه «شارژ حساب» یکی از روش‌ها رو انتخاب کن: درگاه پرداخت آنلاین، کارت به کارت، ترون (TRX) یا گرام (TON). مبلغ بعد از تایید پرداخت به موجودی کیف پولت اضافه می‌شه.\n"
        . "🔹 <b>۲. انتخاب محصول:</b> از «خرید و سرویس‌ها» دسته و محصول دلخواهت رو انتخاب کن. قیمت و توضیحات هر محصول همون‌جا نمایش داده می‌شه.\n"
        . "🔹 <b>۳. ثبت اطلاعات:</b> یوزرنیم گیرنده (مثل <code>@username</code>) رو بفرست؛ برای بوست، یوزرنیم یا لینک کانال/گروه و تعداد بوست رو بفرست.\n"
        . "🔹 <b>۴. تایید سفارش:</b> اطلاعات رو یه بار مرور کن و تایید بزن؛ مبلغ از موجودیت کم و سفارش ثبت می‌شه.\n"
        . "🔹 <b>۵. تحویل:</b> تیم " . TEAM . " سفارش رو بررسی و تحویل می‌ده و نتیجه همون لحظه همین‌جا بهت اطلاع داده می‌شه.\n\n"
        . HR . "\n\n"
        . "💳 <b>نکات شارژ حساب</b>\n\n"
        . "🔹 برای شارژ با درگاه یا کارت به کارت، یک‌بار احراز هویت لازمه (فقط یک بار و برای همیشه).\n"
        . "🔹 در کارت به کارت، بعد از واریز عکس رسید رو بفرست تا بررسی بشه.\n"
        . "🔹 در شارژ با ارز دیجیتال، آدرس و شبکه رو دقیق چک کن و بعد از واریز، مراحل ربات رو تا آخر برو.\n"
        . "🔹 با «انتقال موجودی» می‌تونی از حسابت برای کاربر دیگه موجودی بفرستی.\n\n"
        . "⚠️ <b>قبل از ثبت سفارش حتما چک کن</b>\n\n"
        . "🔹 یوزرنیم یا لینک رو دقیق و بدون اشتباه بنویس.\n"
        . "🔹 حساب گیرنده باید فعال باشه و چت یا کانال باید در دسترس باشه.\n"
        . "🔹 قیمت‌ها لحظه‌ای‌ان؛ قیمت نهایی همون چیزیه که موقع تایید می‌بینی.\n\n"
        . "👮🏻 <b>پشتیبانی</b>\nهر سوال یا مشکلی داشتی از دکمه «پشتیبانی» پیام بده؛ تیم " . TEAM . " کنارته.";
}

function default_rules(): string
{
    return head('📜', 'قوانین و مقررات ' . BRAND)
        . "استفاده از <b>" . BRAND . "</b> یعنی با موارد زیر موافقی. لطفا قبل از خرید با دقت بخون ✨\n\n"
        . "🪪 <b>۱. حساب کاربری</b>\n"
        . "🔹 هر کاربر فقط یک حساب داره و مسئولیت امنیت و فعالیت‌های حسابش با خودشه.\n"
        . "🔹 اطلاعات واردشده (مثل مدارک احراز هویت) باید واقعی و متعلق به خود کاربر باشه.\n\n"
        . "💰 <b>۲. شارژ و موجودی</b>\n"
        . "🔹 شارژ فقط با روش‌های اعلام‌شده در ربات انجام می‌شه و مبلغ بعد از تایید پرداخت به موجودی اضافه می‌شه.\n"
        . "🔹 برای شارژ ریالی (درگاه و کارت به کارت) احراز هویت الزامیه؛ واریز باید از کارتی انجام بشه که به نام خود کاربره.\n"
        . "🔹 در پرداخت با ارز دیجیتال، انتخاب درست شبکه و آدرس با کاربره و واریز اشتباه قابل پیگیری یا بازگشت نیست.\n"
        . "🔹 موجودی کیف پول برای خرید از همین ربات قابل استفاده‌ست.\n\n"
        . "📦 <b>۳. ثبت و تحویل سفارش</b>\n"
        . "🔹 درست بودن یوزرنیم، لینک و تعداد واردشده کاملا با خریداره و بعد از تحویل، اصلاح یا جابه‌جایی ممکن نیست.\n"
        . "🔹 قیمت‌ها لحظه‌ای‌ان و ممکنه با نرخ بازار تغییر کنن؛ قیمت لحظه تایید سفارش ملاکه.\n"
        . "🔹 هر سفارش بعد از بررسی توسط تیم " . TEAM . " تحویل می‌شه و نتیجه از طریق ربات اعلام می‌شه.\n"
        . "🔹 محصولات بوست طبق مدت انتخابی («۱ الی ۵ روزه» یا «۳۰ روزه») ارائه می‌شن و حداقل تعداد سفارش رعایت می‌شه.\n\n"
        . "🔄 <b>۴. لغو و بازگشت وجه</b>\n"
        . "🔹 اگه سفارشی تایید یا تحویل نشه، مبلغ کامل به موجودی کیف پول برمی‌گرده.\n"
        . "🔹 بعد از تحویل موفق سفارش، به دلیل ماهیت دیجیتال و غیرقابل بازگشت محصولات، امکان لغو یا استرداد وجه وجود نداره.\n"
        . "🔹 اگه مشکلی در سفارش پیش اومد، حتما قبل از هر اقدام دیگه با پشتیبانی تماس بگیر.\n\n"
        . "⛔ <b>۵. موارد ممنوع</b>\n"
        . "🔹 ارائه مدارک یا اطلاعات جعلی، استفاده از کارت یا حساب دیگران و هرگونه کلاهبرداری.\n"
        . "🔹 سوءاستفاده از اشکالات ربات یا قیمت‌گذاری و تلاش برای اختلال در سرویس.\n"
        . "🔹 اسپم، توهین یا مزاحمت برای پشتیبانی و سایر کاربران.\n"
        . "🔹 در صورت تخلف، حساب مسدود می‌شه و موجودی طبق تشخیص مدیریت بررسی می‌شه.\n\n"
        . "🛡 <b>۶. حریم خصوصی</b>\n"
        . "🔹 اطلاعات و مدارک شما فقط برای احراز هویت و پیگیری سفارش‌ها استفاده می‌شه و در اختیار شخص ثالث قرار نمی‌گیره.\n\n"
        . "📌 <b>۷. سایر موارد</b>\n"
        . "🔹 " . TEAM . " می‌تونه قیمت‌ها، محصولات و این قوانین رو در هر زمان بروز کنه؛ آخرین نسخه همین‌جا در دسترسه.\n"
        . "🔹 مسئولیت اتفاقاتی مثل محدودیت‌های خود تلگرام یا خطای کاربر در اطلاعات واردشده خارج از کنترل ماست.\n\n"
        . "✅ استفاده از ربات به معنی پذیرش این قوانینه. از اینکه " . BRAND . " رو انتخاب کردی ممنونیم!";
}
function menu_main(int $chat, int $mid = 0): void
{
    screen($chat, $mid, txt_get('start'), kb_main());
}

function welcome_new(int $chat, string $name): void
{
    $name = trim($name) !== '' ? ' ' . h(trim($name)) : '';
    $t  = head('🎉', 'خوش اومدی' . $name . '!');
    $t .= 'به <b>' . BRAND . "</b> رسیدی، خونه‌ی خرید استارز، پریمیوم و گیفت‌های تلگرام ✨\n";
    $t .= 'ما تیم <b>' . TEAM . "</b> هستیم و همه‌چیز رو برات ساده و مطمئن چیدیم:\n\n";
    $t .= "{e:stars} <b>استارز تلگرام</b>\nتعداد دلخواهت رو بخر، مستقیم به اکانتت می‌شینه\n\n";
    $t .= "{e:premium} <b>اشتراک پریمیوم</b>\n۳، ۶ و ۱۲ ماهه با قیمت روز\n\n";
    $t .= "🎁 <b>گیفت‌های استارزی</b>\nتدی، گل رز، کیک تولد، الماس و کلی هدیه‌ی دیگه برای عزیزانت\n\n";
    $t .= "{e:boost} <b>بوست کانال و گروه</b>\nکانالت رو به لول بالاتر برسون\n\n";
    $t .= "🔹 قیمت‌ها لحظه‌ای و بدون واسطه بروز می‌شن\n";
    $t .= "🔹 حسابت رو شارژ کن، با چند کلیک سفارش بده\n";
    $t .= "🔹 پشتیبانی همیشه کنارته\n\n";
    $t .= "👇 از دکمه‌های زیر شروع کن، امیدواریم تجربه‌ی خوبی داشته باشی";
    Tg::send($chat, $t, kb_main());
}

function brand_sync(): void
{
    if (Db::kv('brand_v', '') === '2') {
        return;
    }
    $ok = true;
    $r  = Tg::call('setMyName', ['name' => BRAND], 10);
    $ok = $ok && !empty($r['ok']);
    $r  = Tg::call('setMyShortDescription', ['short_description' => 'فروشگاه استارز، پریمیوم، گیفت و بوست تلگرام | تیم ' . TEAM], 10);
    $ok = $ok && !empty($r['ok']);
    $r  = Tg::call('setMyDescription', ['description' => BRAND . " | تیم " . TEAM . "\n\nخرید سریع و مطمئن استارز تلگرام، اشتراک پریمیوم، گیفت‌های استارزی (تدی، گل رز، کیک تولد و ...) و بوست کانال و گروه.\n\nقیمت‌های لحظه‌ای، تحویل سریع و پشتیبانی همیشه همراه.\n\nبرای شروع Start رو بزن."], 10);
    $ok = $ok && !empty($r['ok']);
    if ($ok) {
        Db::kvSet('brand_v', '2');
    }
}

function prompt(int $chat, string $step, string $text, bool $withBack = true): void
{
    set_step($chat, $step);
    Tg::send($chat, $text, $withBack ? kb_back() : null);
}

function admin_done(int $chat, string $text): void
{
    set_step($chat, 'none');
    Tg::send($chat, $text, kb_panel());
}

/* ======================================================================
 *  URLs / webhook
 * ==================================================================== */

function env_base_url(): string
{
    $w = env('WEB_URL');
    if ($w !== '') {
        return rtrim(preg_match('#^https?://#i', $w) ? $w : 'https://' . $w, '/');
    }
    $d = env('RAILWAY_PUBLIC_DOMAIN');
    if ($d !== '') {
        return 'https://' . $d;
    }
    return '';
}

function base_url(): string
{
    $b = env_base_url();
    if ($b !== '') {
        return $b;
    }
    $host = trim(explode(',', (string)($_SERVER['HTTP_X_FORWARDED_HOST'] ?? ($_SERVER['HTTP_HOST'] ?? '')))[0]);
    if ($host === '' || str_contains($host, 'healthcheck.railway.app')
        || str_starts_with($host, 'localhost') || str_starts_with($host, '127.')) {
        return '';
    }
    $proto = trim(explode(',', (string)($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? 'https'))[0]);
    return ($proto === 'http' ? 'http' : 'https') . '://' . $host;
}

function webhook_secret(): string
{
    return hash_hmac('sha256', 'telegram-webhook', Config::$token);
}

function set_webhook(string $base): array
{
    $url = rtrim($base, '/') . '/webhook';
    $r   = Tg::call('setWebhook', [
        'url'                  => $url,
        'secret_token'         => webhook_secret(),
        'allowed_updates'      => ['message', 'callback_query'],
        'max_connections'      => 40,
        'drop_pending_updates' => false,
    ]);
    $ok = (bool)($r['ok'] ?? false);
    if ($ok) {
        @file_put_contents(Config::$dataDir . '/.webhook', $url . '|' . sha1(Config::$token));
    }
    return ['ok' => $ok, 'url' => $url, 'description' => $r['description'] ?? ''];
}

function ensure_webhook(): void
{
    if (Config::$token === '') {
        return;
    }
    $base = base_url();
    if ($base === '') {
        return;
    }
    $want = $base . '/webhook|' . sha1(Config::$token);
    $cur  = @file_get_contents(Config::$dataDir . '/.webhook');
    if ($cur === $want) {
        return;
    }
    $try = Config::$dataDir . '/.webhook_try';
    if (is_file($try) && time() - (int)@filemtime($try) < 30) {
        return;
    }
    @touch($try);
    $r = set_webhook($base);
    logx('auto webhook ' . ($r['ok'] ? 'set: ' : 'FAILED: ') . $r['url'] . ' ' . $r['description']);
}

function bot_username(): string
{
    $u = ltrim(env('BOT_USERNAME'), '@');
    if ($u !== '') {
        return $u;
    }
    $f = Config::$dataDir . '/.botname';
    $c = @file_get_contents($f);
    if ($c !== false && $c !== '') {
        return trim($c);
    }
    $r = Tg::call('getMe', [], 10);
    $n = (string)($r['result']['username'] ?? '');
    if ($n !== '') {
        @file_put_contents($f, $n);
    }
    return $n;
}

/* ======================================================================
 *  Access gates
 * ==================================================================== */

function bot_id(): int
{
    return (int)explode(':', Config::$token)[0];
}

function fj_enabled(): bool
{
    return Db::kv('fj_on', 'on') === 'on';
}

function fj_list(): array
{
    $j   = json_decode(Db::kv('fj_channels', '[]'), true);
    $out = [];
    foreach (is_array($j) ? $j : [] as $c) {
        if (is_array($c) && !empty($c['id'])) {
            $out[] = [
                'id'    => (string)$c['id'],
                'title' => (string)($c['title'] ?? $c['id']),
                'link'  => (string)($c['link'] ?? ''),
            ];
        }
    }
    return $out;
}

function fj_save(array $list): void
{
    Db::kvSet('fj_channels', json_encode(array_values($list), JSON_UNESCAPED_UNICODE));
}

function fj_key(string $id): string
{
    return substr(md5($id), 0, 8);
}

function fj_chat_id(string $id)
{
    return preg_match('/^-?\d+$/', $id) ? (int)$id : $id;
}

function missing_channels(int $uid, bool $fresh = false): array
{
    if (!fj_enabled()) {
        return [];
    }
    $missing = [];
    $now     = time();
    foreach (fj_list() as $ch) {
        if (!$fresh) {
            $ts = Db::val('SELECT ts FROM joincache WHERE uid = ? AND ch = ?', [$uid, $ch['id']]);
            if ($ts !== null && $now - (int)$ts < JOIN_CACHE_TTL) {
                continue;
            }
        }
        $r = Tg::call('getChatMember', ['chat_id' => fj_chat_id($ch['id']), 'user_id' => $uid], 10);
        if (!$r || empty($r['ok'])) {
            continue;
        }
        $st = $r['result']['status'] ?? 'left';
        $in = in_array($st, ['creator', 'administrator', 'member'], true)
            || ($st === 'restricted' && !empty($r['result']['is_member']));
        if ($in) {
            Db::exec('INSERT OR REPLACE INTO joincache (uid, ch, ts) VALUES (?,?,?)', [$uid, $ch['id'], $now]);
        } else {
            Db::exec('DELETE FROM joincache WHERE uid = ? AND ch = ?', [$uid, $ch['id']]);
            $missing[] = $ch;
        }
    }
    return $missing;
}

function gate(int $uid, bool $admin, int $chat, array $user, ?string $cbId = null, bool $skipChannels = false): bool
{
    if ($admin) {
        return true;
    }
    $deny = function (string $text) use ($chat, $cbId): bool {
        if ($cbId !== null) {
            Tg::answer($cbId, $text, true);
        } else {
            Tg::send($chat, $text);
        }
        return false;
    };

    if ((Db::setting()['bot'] ?? 'on') === 'off') {
        return $deny('⛔ ربات فعلا در حال بروزرسانیه، کمی بعد دوباره سر بزن 🙏');
    }
    if (($user['account'] ?? '') === 'ban') {
        return $deny('⛔ متاسفانه دسترسیت به ربات مسدود شده. اگه فکر می‌کنی اشتباهه به پشتیبانی پیام بده.');
    }
    if (!$skipChannels) {
        $missing = missing_channels($uid);
        if ($missing) {
            $rows = [];
            foreach ($missing as $ch) {
                if ($ch['link'] !== '') {
                    $rows[] = [ub('📢 ' . $ch['title'], $ch['link'])];
                }
            }
            $rows[] = [cb('✅ عضو شدم', 'joined')];
            if ($cbId !== null) {
                Tg::answer($cbId, 'اول توی کانال‌ها عضو شو 🙏', true);
            }
            Tg::send(
                $chat,
                head('🔒', 'یه قدم تا شروع!')
                . 'برای استفاده از ' . BRAND . ' فقط کافیه توی کانال' . (count($missing) > 1 ? '‌های' : '') . " زیر عضو بشی، بعدش همه‌چیز برات باز می‌شه ✨\n\n"
                . '👇 بعد از عضویت روی «عضو شدم» بزن',
                ik($rows)
            );
            return false;
        }
    }
    return true;
}

/* ======================================================================
 *  HTTP helper (external APIs)
 * ==================================================================== */

function http_json(string $url, ?array $post = null, array $headers = [], int $timeout = 20): ?array
{
    $ch = curl_init($url);
    $h  = array_merge(['Accept: application/json'], $headers);
    $o  = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT        => $timeout,
        CURLOPT_FOLLOWLOCATION => false,
    ];
    if ($post !== null) {
        $o[CURLOPT_POST]       = true;
        $o[CURLOPT_POSTFIELDS] = json_encode($post, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $h[]                   = 'Content-Type: application/json';
    }
    $o[CURLOPT_HTTPHEADER] = $h;
    curl_setopt_array($ch, $o);
    $raw = curl_exec($ch);
    if ($raw === false) {
        logx('http error: ' . curl_error($ch));
        curl_close($ch);
        return null;
    }
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ['code' => $code, 'json' => json_decode((string)$raw, true)];
}

/* ======================================================================
 *  Exchange rates (TRX / TON -> Toman)
 * ==================================================================== */

function json_flatten($j, string $prefix, array &$out): void
{
    if (is_array($j)) {
        foreach ($j as $k => $v) {
            json_flatten($v, $prefix === '' ? (string)$k : $prefix . '.' . $k, $out);
        }
        return;
    }
    $out[$prefix] = $j;
}

function num_of($v): ?float
{
    if (is_int($v) || is_float($v)) {
        return (float)$v;
    }
    if (is_string($v)) {
        $c = str_replace(',', '', trim($v));
        return is_numeric($c) ? (float)$c : null;
    }
    return null;
}

function json_pick_number($j, string $path): ?float
{
    $path = trim($path);
    if ($path !== '' && $path !== '-') {
        $cur = $j;
        foreach (explode('.', $path) as $k) {
            if (is_array($cur) && array_key_exists($k, $cur)) {
                $cur = $cur[$k];
            } elseif (is_array($cur) && ctype_digit($k) && array_key_exists((int)$k, $cur)) {
                $cur = $cur[(int)$k];
            } else {
                return null;
            }
        }
        return num_of($cur);
    }
    $flat = [];
    json_flatten($j, '', $flat);
    $prefer = ['price', 'last', 'latest', 'last_price', 'lastprice', 'rate', 'close', 'value'];
    foreach ($flat as $k => $v) {
        $leaf = strtolower((string)substr((string)strrchr('.' . $k, '.'), 1));
        if (in_array($leaf, $prefer, true) && ($n = num_of($v)) !== null && $n > 0) {
            return $n;
        }
    }
    foreach ($flat as $v) {
        if (($n = num_of($v)) !== null && $n > 0) {
            return $n;
        }
    }
    return null;
}

function rate_mode(string $c): string
{
    $m = Db::kv("rate_{$c}_mode", 'manual');
    return in_array($m, ['manual', 'auto', 'api'], true) ? $m : 'manual';
}

function rate_from_api(string $url, string $path, string $unit, ?string &$err): ?int
{
    if (!safe_url($url)) {
        $err = 'آدرس API نامعتبر است';
        return null;
    }
    $r = http_json($url, null, [], 15);
    if (!$r || $r['code'] !== 200 || !is_array($r['json'])) {
        $err = 'پاسخ معتبر از API دریافت نشد' . ($r ? ' (HTTP ' . $r['code'] . ')' : '');
        return null;
    }
    $v = json_pick_number($r['json'], $path);
    if ($v === null || $v <= 0) {
        $err = 'عدد قیمت در پاسخ API پیدا نشد (مسیر را بررسی کنید)';
        return null;
    }
    return (int)round($unit === 'rial' ? $v / 10 : $v);
}

function rate_from_nobitex(string $c, ?string &$err): ?int
{
    $sym = COINS[$c]['nob'];
    $r   = http_json('https://api.nobitex.ir/market/stats?srcCurrency=' . $sym . '&dstCurrency=rls', null, [], 15);
    $v   = $r['json']['stats'][$sym . '-rls']['latest'] ?? null;
    if (!is_numeric($v) || (float)$v <= 0) {
        $err = 'دریافت نرخ از نوبیتکس ممکن نشد' . ($r ? ' (HTTP ' . $r['code'] . ')' : '');
        return null;
    }
    return (int)round((float)$v / 10);
}

function rate_fetch(string $c, ?string &$err = null): ?int
{
    $mode = rate_mode($c);
    if ($mode === 'auto') {
        return rate_from_nobitex($c, $err);
    }
    if ($mode === 'api') {
        return rate_from_api(Db::kv("rate_{$c}_api_url"), Db::kv("rate_{$c}_api_path"), Db::kv("rate_{$c}_api_unit", 'toman'), $err);
    }
    return null;
}

function rate_get(string $c, bool $force = false, int $ttl = RATE_TTL): int
{
    if (!isset(COINS[$c])) {
        return 0;
    }
    if (rate_mode($c) === 'manual') {
        return max(0, (int)Db::kv("rate_{$c}_manual", '0'));
    }
    $val = (int)Db::kv("rate_{$c}_val", '0');
    $ts  = (int)Db::kv("rate_{$c}_ts", '0');
    $age = time() - $ts;
    $try = (int)Db::kv("rate_{$c}_try", '0');

    if ($force || $val <= 0 || $age > $ttl) {
        if (!$force && time() - $try < ($ttl < 60 ? 5 : 60)) {
            return $age <= RATE_STALE_MAX ? $val : 0;
        }
        Db::kvSet("rate_{$c}_try", (string)time());
        $err = null;
        $n   = rate_fetch($c, $err);
        if ($n !== null && $n > 0) {
            Db::kvSet("rate_{$c}_val", (string)$n);
            Db::kvSet("rate_{$c}_ts", (string)time());
            Db::kvSet("rate_{$c}_err", '');
            return $n;
        }
        Db::kvSet("rate_{$c}_err", (string)$err);
        return $age <= RATE_STALE_MAX ? $val : 0;
    }
    return $val;
}

function rate_note(int $rate, string $unit): string
{
    return $rate > 0
        ? "\n💱 نرخ تبدیل: هر 1 $unit = " . money($rate) . ' تومان (شارژ خودکار)'
        : "\n⏳ پس از بررسی، ادمین موجودی شما را شارژ می‌کند.";
}

/* ======================================================================
 *  Fragment stars pricing
 * ==================================================================== */

function sp_enabled(): bool
{
    return Db::kv('sp_on', 'on') === 'on';
}

function sp_margin(): float
{
    return max(0.0, (float)Db::kv('sp_margin', '10'));
}

function sp_round(): int
{
    return max(1, (int)Db::kv('sp_round', '1000'));
}

function pm_custom(array $p): ?float
{
    $v = trim(Db::kv('pm_' . (int)$p['id'], ''));
    return $v === '' ? null : max(0.0, (float)$v);
}

function p_margin(array $p): float
{
    return pm_custom($p) ?? sp_margin();
}

function pm_fmt(float $f): string
{
    return rtrim(rtrim(sprintf('%.2F', $f), '0'), '.') ?: '0';
}

function sp_calc(float $ton, int $rate, ?float $margin = null): int
{
    $raw  = $ton * $rate * (1 + ($margin ?? sp_margin()) / 100);
    $step = sp_round();
    return (int)(ceil($raw / $step) * $step);
}

function p_auto_key(array $p): ?string
{
    $n = (int)($p['number'] ?? 0);
    $t = p_type($p);
    if ($t === 'stars') {
        return ($n >= 50 && $n <= 10000000) ? 's:' . $n : null;
    }
    if ($t === 'permium') {
        return in_array($n, [3, 6, 12], true) ? 'p:' . $n : null;
    }
    return null;
}

function p_is_auto(array $p): bool
{
    return strtolower(trim((string)($p['Fragment'] ?? ''))) === 'auto' && p_auto_key($p) !== null;
}

function fragment_prices(array $qtys, ?string &$err = null): array
{
    $out = [];
    $ch  = curl_init('https://fragment.com/stars/buy');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_COOKIEFILE     => '',
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS      => 3,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_ENCODING       => '',
        CURLOPT_USERAGENT      => FRAGMENT_UA,
        CURLOPT_HTTPHEADER     => ['Accept: text/html,application/xhtml+xml', 'Accept-Language: en-US,en;q=0.9'],
    ]);
    $html = curl_exec($ch);
    if (!is_string($html) || !preg_match('~api\?hash=([0-9a-f]+)~', $html, $mm)) {
        $err = 'اتصال به Fragment.com برقرار نشد یا ساختار سایت تغییر کرده است';
        curl_close($ch);
        return [];
    }
    curl_setopt_array($ch, [
        CURLOPT_URL        => 'https://fragment.com/api?hash=' . $mm[1],
        CURLOPT_POST       => true,
        CURLOPT_HTTPHEADER => [
            'Accept: application/json, text/javascript, */*; q=0.01',
            'X-Requested-With: XMLHttpRequest',
            'Origin: https://fragment.com',
            'Referer: https://fragment.com/stars/buy',
        ],
    ]);
    foreach ($qtys as $q) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query(['stars' => '', 'quantity' => (int)$q, 'method' => 'updateStarsPrices']));
        $raw = curl_exec($ch);
        $j   = is_string($raw) ? json_decode($raw, true) : null;
        $cp  = is_array($j) ? (string)($j['cur_price'] ?? '') : '';
        if (!preg_match('~icon-ton">\s*([\d,]+)(?:<span class="mini-frac">(\.\d+)</span>)?~', $cp, $t)) {
            $err = is_array($j) && !empty($j['error']) ? 'Fragment: ' . strip_tags((string)$j['error']) : 'قیمت از Fragment دریافت نشد';
            continue;
        }
        $ton = (float)(str_replace(',', '', $t[1]) . ($t[2] ?? ''));
        $usd = preg_match('~icon-usd">\s*([\d,\.]+)</div>~', $cp, $u) ? (float)str_replace(',', '', $u[1]) : 0.0;
        if ($ton > 0) {
            $out[(int)$q] = ['ton' => $ton, 'usd' => $usd, 'ts' => time()];
        }
        usleep(150000);
    }
    curl_close($ch);
    return $out;
}

function fragment_premium_prices(?string &$err = null): array
{
    $ch = curl_init('https://fragment.com/premium/gift');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_COOKIEFILE     => '',
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS      => 3,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_ENCODING       => '',
        CURLOPT_USERAGENT      => FRAGMENT_UA,
        CURLOPT_HTTPHEADER     => ['Accept: text/html,application/xhtml+xml', 'Accept-Language: en-US,en;q=0.9'],
    ]);
    $html = curl_exec($ch);
    curl_close($ch);
    $out = [];
    if (is_string($html) && preg_match_all('~name="months"\s+value="(\d+)".*?</label>~s', $html, $blocks, PREG_SET_ORDER)) {
        foreach ($blocks as $b) {
            if (!preg_match('~icon-ton">\s*([\d,]+)(?:<span class="mini-frac">(\.\d+)</span>)?~', $b[0], $t)) {
                continue;
            }
            $ton = (float)(str_replace(',', '', $t[1]) . ($t[2] ?? ''));
            $usd = preg_match('~tm-radio-desc">(?:&#036;|\$)\s*([\d,\.]+)~', $b[0], $u) ? (float)str_replace(',', '', $u[1]) : 0.0;
            if ($ton > 0) {
                $out[(int)$b[1]] = ['ton' => $ton, 'usd' => $usd, 'ts' => time()];
            }
        }
    }
    if (!$out) {
        $err = 'دریافت قیمت پرمیوم از Fragment.com ممکن نشد یا ساختار سایت تغییر کرده است';
    }
    return $out;
}

function fp_cache(): array
{
    $c = json_decode(Db::kv('fp_cache', '{}'), true);
    return is_array($c) ? $c : [];
}

function sp_refresh(bool $force = false, ?int $onlyPid = null): array
{
    $res = ['ok' => true, 'err' => '', 'changes' => [], 'checked' => 0, 'skipped' => false];
    if (!$force && !sp_enabled()) {
        $res['skipped'] = true;
        return $res;
    }
    $sql    = "SELECT * FROM ProductsF WHERE LOWER(TRIM(Fragment)) = 'auto'";
    $params = [];
    if ($onlyPid !== null) {
        $sql     .= ' AND id = ?';
        $params[] = $onlyPid;
    }
    $prods = array_values(array_filter(Db::rows($sql, $params), 'p_is_auto'));
    if (!$prods) {
        return $res;
    }

    $cache = fp_cache();
    $needS = [];
    $needP = false;
    foreach ($prods as $p) {
        $k = (string)p_auto_key($p);
        $c = $cache[$k] ?? null;
        if ($force || !is_array($c) || time() - (int)$c['ts'] > SP_TTL) {
            if ($k[0] === 's') {
                $needS[(int)substr($k, 2)] = true;
            } else {
                $needP = true;
            }
        }
    }
    $err = null;
    if (($needS || $needP) && ($force || time() - (int)Db::kv('sp_try', '0') >= 60)) {
        Db::kvSet('sp_try', (string)time());
        if ($needS) {
            foreach (fragment_prices(array_keys($needS), $err) as $q => $v) {
                $cache['s:' . $q] = $v;
            }
        }
        if ($needP) {
            $e2 = null;
            foreach (fragment_premium_prices($e2) as $mo => $v) {
                $cache['p:' . $mo] = $v;
            }
            $err = $err ?: $e2;
        }
        Db::kvSet('fp_cache', json_encode($cache));
    }

    $rate = rate_get('ton', $force, RATE_LIVE_TTL);
    if ($rate <= 0) {
        $res['ok']  = false;
        $res['err'] = 'نرخ گرام (TON) تنظیم نشده یا دریافت نشد';
        Db::kvSet('sp_err', $res['err']);
        return $res;
    }
    $latest = 0;
    foreach ($prods as $p) {
        $c = $cache[(string)p_auto_key($p)] ?? null;
        if (!is_array($c) || time() - (int)$c['ts'] > SP_STALE_MAX) {
            continue;
        }
        $res['checked']++;
        $latest = max($latest, (int)$c['ts']);
        $new    = sp_calc((float)$c['ton'], $rate, p_margin($p));
        $old    = (int)$p['price'];
        if ($new !== $old) {
            Db::exec('UPDATE ProductsF SET price = ? WHERE id = ?', [(string)$new, (int)$p['id']]);
            $res['changes'][] = [
                'name'  => (string)$p['name'],
                'label' => p_qty($p),
                'old'   => $old,
                'new'   => $new,
                'ton'   => (float)$c['ton'],
            ];
        }
    }
    if ($res['checked'] === 0) {
        $res['ok']  = false;
        $res['err'] = $err ?: 'قیمتی از Fragment دریافت نشد';
    } else {
        $res['err'] = (string)$err;
        Db::kvSet('sp_ts', (string)$latest);
    }
    Db::kvSet('sp_err', $res['err']);
    return $res;
}

function sp_lazy(): void
{
    if (!sp_enabled()) {
        return;
    }
    try {
        sp_refresh(false);
    } catch (Throwable $e) {
        logx('sp_lazy failed: ' . $e->getMessage());
    }
}

function sp_notify_changes(): array
{
    $map = json_decode(Db::kv('sp_notified', '{}'), true);
    if (!is_array($map)) {
        $map = [];
    }
    $out = [];
    foreach (Db::rows("SELECT * FROM ProductsF WHERE LOWER(TRIM(Fragment)) = 'auto'") as $p) {
        if (!p_is_auto($p)) {
            continue;
        }
        $id  = (string)$p['id'];
        $cur = (int)$p['price'];
        $old = (int)($map[$id] ?? 0);
        if ($old <= 0) {
            $map[$id] = $cur;
            continue;
        }
        if ($cur > 0 && abs($cur - $old) / $old * 100 >= SP_NOTIFY_PCT) {
            $c     = fp_cache()[(string)p_auto_key($p)] ?? [];
            $out[] = [
                'name'  => (string)$p['name'],
                'label' => p_qty($p),
                'old'   => $old,
                'new'   => $cur,
                'ton'   => (float)($c['ton'] ?? 0),
            ];
            $map[$id] = $cur;
        }
    }
    Db::kvSet('sp_notified', json_encode($map));
    return $out;
}

function sp_report(array $changes): string
{
    $t = "⭐ <b>قیمت جدید (Fragment)</b>\n";
    foreach ($changes as $c) {
        $pct = $c['old'] > 0 ? sprintf('%+.1f%%', ($c['new'] - $c['old']) / $c['old'] * 100) : 'جدید';
        $dir = $c['new'] >= $c['old'] ? '📈' : '📉';
        $t  .= "\n$dir " . h($c['name']) . ' (' . $c['label'] . ")\n"
            . '   ' . money($c['old']) . ' ← <b>' . money($c['new']) . '</b> تومان (' . $pct . ')'
            . ($c['ton'] > 0 ? ' — ' . rtrim(rtrim(sprintf('%.4F', $c['ton']), '0'), '.') . ' TON' : '');
    }
    return $t;
}

/* ======================================================================
 *  Products / orders
 * ==================================================================== */

function p_type(array $p): string
{
    $t = strtolower(trim((string)($p['startsorpermium'] ?? '')));
    if (in_array($t, ['stars', 'starts', 'star'], true)) {
        return 'stars';
    }
    if (in_array($t, ['permium', 'premium'], true)) {
        return 'permium';
    }
    if ($t === 'gift') {
        return 'gift';
    }
    if ($t === 'boost') {
        return 'boost';
    }
    return '';
}

function p_ready(array $p): bool
{
    return p_type($p) !== '' && (int)$p['price'] > 0
        && trim((string)$p['ProductsA']) !== '' && $p['ProductsA'] !== 'none';
}

function toggle_on(string $col): bool
{
    if (str_starts_with($col, 'k_')) {
        return Db::kv($col, 'on') === 'on';
    }
    return (Db::setting()[$col] ?? 'on') === 'on';
}

function p_enabled(array $p): bool
{
    if (!toggle_on('sell')) {
        return false;
    }
    return match (p_type($p)) {
        'stars'   => toggle_on('stars'),
        'permium' => toggle_on('permium'),
        'gift'    => toggle_on('k_gift'),
        'boost'   => toggle_on('k_boost'),
        default   => false,
    };
}

function boost_kind(array $p): string
{
    return (int)($p['number'] ?? 0) >= 30 ? 'l' : 's';
}

function boost_min(): int
{
    return max(1, (int)Db::kv('boost_min', (string)BOOST_MIN_DEF));
}

function p_qty(array $p): string
{
    $n = (int)$p['number'];
    switch (p_type($p)) {
        case 'stars':
            return "{e:stars} $n استارز";
        case 'gift':
            $g = GIFTS[$n] ?? null;
            return $g ? '{e:g' . $n . '} گیفت ' . $g['name'] . ' (' . $g['stars'] . ' استارز)' : '{e:g3} گیفت استارزی';
        case 'boost':
            return '{e:boost} ' . BOOSTS[boost_kind($p)]['name'];
        default:
            return "{e:premium} $n ماهه";
    }
}

function unit_price_key(array $p): ?string
{
    return match (p_type($p)) {
        'gift'  => 'gift_price_' . (int)$p['number'],
        'boost' => 'boost_price_' . boost_kind($p),
        default => null,
    };
}

function unit_price_set(array $p, int $price): void
{
    $key = unit_price_key($p);
    if ($key === null) {
        return;
    }
    Db::kvSet($key, (string)$price);
    Db::exec(
        'UPDATE ProductsF SET price = ? WHERE LOWER(TRIM(startsorpermium)) = ? AND CAST(number AS INTEGER) = ?',
        [(string)$price, p_type($p), (int)$p['number']]
    );
}

function status_label(string $r): string
{
    return match ($r) {
        'compile'    => '✅ تحویل شد',
        'NotCompile' => '❌ رد شد',
        default      => '⏳ در انتظار',
    };
}

function order_create(int $uid, array $p, string $account, ?int $total = null): ?string
{
    $price = $total ?? (int)$p['price'];
    $oid   = bin2hex(random_bytes(6));
    $ok    = Db::tx(function () use ($uid, $p, $account, $price, $oid) {
        if (!coin_sub($uid, $price)) {
            return false;
        }
        Db::exec(
            'INSERT INTO Orders (id, products_id, user, user_id, time, date, price, result) VALUES (?,?,?,?,?,?,?,?)',
            [$oid, (string)$p['id'], (string)$uid, $account, Jalali::time(), Jalali::date(), (string)$price, 'Incomplete']
        );
        return true;
    });
    return $ok ? $oid : null;
}

/* ======================================================================
 *  User-facing callbacks
 * ==================================================================== */

function p_icon(array $p): string
{
    switch (p_type($p)) {
        case 'stars':
            return '{e:stars}';
        case 'gift':
            $n = (int)$p['number'];
            return isset(GIFTS[$n]) ? '{e:g' . $n . '}' : '{e:g3}';
        case 'boost':
            return '{e:boost}';
        default:
            return '{e:premium}';
    }
}

function p_default_name(array $p): string
{
    $n = (int)$p['number'];
    switch (p_type($p)) {
        case 'stars':
            return "$n استارز";
        case 'gift':
            return 'گیفت ' . (GIFTS[$n]['name'] ?? 'استارزی');
        case 'boost':
            return BOOSTS[boost_kind($p)]['name'];
        default:
            return "پریمیوم $n ماهه";
    }
}

function p_title(array $p): string
{
    $n = Pe::strip((string)$p['name']);
    return ($n === '' || $n === '-') ? p_default_name($p) : $n;
}

function p_autoname(int $pid): void
{
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if ($p && in_array(trim((string)$p['name']), ['', '-'], true)) {
        Db::exec('UPDATE ProductsF SET name = ? WHERE id = ?', [p_default_name($p), $pid]);
    }
}

function p_banner(array $p, int $bal): string
{
    $type  = p_type($p);
    $n     = (int)$p['number'];
    $title = h(p_title($p));
    $boost = $type === 'boost';
    $need  = $boost ? (int)$p['price'] * boost_min() : (int)$p['price'];

    $t = head(p_icon($p), $title);
    switch ($type) {
        case 'stars':
            $t .= "ستاره‌های تلگرام رو راحت و مستقیم برای اکانتت (یا هر کسی که بخوای) می‌فرستیم ✨\n\n"
                . "🔹 تحویل مستقیم به یوزرنیمی که می‌دی\n"
                . "🔹 قیمت لحظه‌ای و مطابق نرخ روز\n"
                . "🔹 مناسب خرید گیفت، حمایت از کانال‌ها و استفاده توی ربات‌ها\n";
            break;
        case 'gift':
            $g  = GIFTS[$n] ?? null;
            $t .= 'یه هدیه‌ی خاص از طرف تو! گیفت <b>' . h($g['name'] ?? 'استارزی') . '</b>'
                . ($g ? ' با ارزش <b>' . $g['stars'] . ' استارز</b>' : '')
                . " مستقیم برای گیرنده فرستاده می‌شه 🎁\n\n"
                . "🔹 فقط یوزرنیم گیرنده رو بده، بقیه‌ش با ما\n"
                . "🔹 هدیه‌ای که حسابی توی چشمه و یادگاری می‌مونه\n"
                . "🔹 مناسب تولد، سالگرد و هر مناسبت خاص\n";
            break;
        case 'boost':
            $t .= "کانال یا گروهت رو با بوست به لول بالاتر برسون و قابلیت‌های جدیدش رو باز کن {e:bolt}\n\n"
                . '🔹 ' . (boost_kind($p) === 'l' ? 'ماندگاری ۳۰ روزه، تضمینی' : 'ماندگاری ۱ تا ۵ روز، تضمینی') . "\n"
                . "🔹 مناسب کانال‌ها و گروه‌های عمومی\n"
                . "🔹 فقط لینک یا یوزرنیم کانال/گروه رو بفرست و تعداد بوست رو بگو\n";
            break;
        default:
            $t .= "اشتراک رسمی <b>Telegram Premium</b> برای <b>$n ماه</b> روی اکانت خودت یا هر کسی که بخوای {e:premium}\n\n"
                . "🔹 ایموجی و استیکرهای ویژه\n"
                . "🔹 آپلود فایل تا ۴ گیگابایت و دانلود سریع‌تر\n"
                . "🔹 حذف تبلیغات و کلی قابلیت انحصاری\n"
                . "🔹 بدون نیاز به ورود به اکانت، فقط یوزرنیم کافیه\n";
    }
    $d = clean_desc($p['Description']);
    if ($d !== '') {
        $t .= "\n📝 " . $d . "\n";
    }
    $t .= "\n" . HR . "\n";
    $t .= "📦 مقدار: <b>" . p_qty($p) . "</b>\n";
    $t .= $boost
        ? '💰 قیمت هر بوست: <b>' . money($p['price']) . "</b> تومان\n"
            . '📌 حداقل سفارش: <b>' . boost_min() . '</b> بوست (' . money($need) . " تومان)\n"
        : '💰 قیمت: <b>' . money($p['price']) . "</b> تومان\n";
    if (p_is_auto($p)) {
        $t .= '🔄 قیمت لحظه‌ای، آخرین بروزرسانی: ' . Jalali::time() . "\n";
    }
    $t .= '👛 موجودی تو: <b>' . money($bal) . "</b> تومان\n";
    $t .= "\n🛡 بعد از ثبت، تیم " . TEAM . ' سفارشت رو بررسی و تحویل می‌ده.';
    return $t;
}

function cb_account(int $chat, int $uid, int $mid): void
{
    $u      = user_get($uid);
    $orders = Db::rows(
        'SELECT o.*, p.name AS pname FROM Orders o LEFT JOIN ProductsF p ON p.id = o.products_id
         WHERE o.user = ? ORDER BY o.rowid DESC LIMIT 5',
        [(string)$uid]
    );
    $total = (int)Db::val('SELECT COUNT(*) FROM Orders WHERE user = ?', [(string)$uid]);

    $t  = head('👤', 'حساب کاربری من');
    $t .= "🆔 آیدی عددی: <code>$uid</code>\n";
    if (trim((string)$u['number']) !== '' && $u['number'] !== '0') {
        $t .= '📞 شماره: ' . h($u['number']) . "\n";
    }
    $t .= '💰 موجودی: <b>' . money($u['coin']) . "</b> تومان\n";
    $t .= '📅 عضویت از: ' . h($u['date']) . ' ' . h($u['time']) . "\n";
    $t .= "📦 تعداد سفارش‌ها: <b>$total</b>";
    if ($orders) {
        $t .= "\n\n🧾 <b>آخرین سفارش‌هات</b>\n";
        foreach ($orders as $o) {
            $t .= "\n🔹 " . h(Pe::strip((string)($o['pname'] ?? 'سرویس حذف‌شده'))) . ' — ' . money($o['price']) . ' ت — ' . status_label((string)$o['result']);
        }
    }
    screen($chat, $mid, $t, ik([
        [cb('💸 انتقال موجودی', 'transfer'), cb(BTN['topup'], 'add_coin')],
        [cb('🏠 منوی اصلی', 'home')],
    ]));
}

function cb_help(int $chat, int $mid): void
{
    screen($chat, $mid, head('🚦', 'راهنما و قوانین') . "هر چیزی که برای یه خرید راحت لازم داری اینجاست 👇", ik([
        [cb('📜 قوانین', 'rules'), cb('📖 راهنما', 'guide')],
        [cb('🏠 منوی اصلی', 'home')],
    ]));
}

function cb_text(int $chat, string $col): void
{
    $t = txt_get($col);
    Tg::send($chat, $t !== '' ? $t : 'هنوز متنی ثبت نشده.', ik([[cb('🏠 منوی اصلی', 'home')]]));
}

function cb_services(int $chat, int $mid): void
{
    if ((Db::setting()['sell'] ?? 'on') !== 'on') {
        screen($chat, $mid, head('⛔', 'فروشگاه بسته است') . 'فعلا فروش متوقف شده، کمی بعد دوباره سر بزن 🙏', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return;
    }
    $cats = Db::rows('SELECT id, name FROM ProductsA ORDER BY rowid');
    if (!$cats) {
        screen($chat, $mid, head('⛔', 'هنوز چیزی اضافه نشده') . 'به‌زودی سرویس‌های جدید می‌رسه، منتظر ما باش!', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return;
    }
    $btns = [];
    foreach ($cats as $c) {
        $btns[] = cb('{e:bag} ' . $c['name'], 'hello,' . $c['id']);
    }
    $rows   = array_chunk($btns, 2);
    $rows[] = [cb('🏠 منوی اصلی', 'home')];
    screen(
        $chat,
        $mid,
        head('{e:cart}', 'ویترین ' . BRAND)
        . "هر بخشی که دوست داری رو انتخاب کن، قیمت‌ها همیشه بروز و لحظه‌ایه ✨\n\n"
        . "{e:stars} استارز  |  {e:premium} پریمیوم  |  🎁 گیفت  |  {e:boost} بوست\n\n"
        . '👇 یکی رو انتخاب کن',
        ik($rows)
    );
}

function cb_category(int $chat, int $mid, int $cid): void
{
    $cat = Db::row('SELECT * FROM ProductsA WHERE id = ?', [$cid]);
    if (!$cat) {
        screen($chat, $mid, '⛔ این بخش پیدا نشد.', ik([[cb('◀️ بازگشت', 'my_bots')]]));
        return;
    }
    sp_lazy();
    $items = Db::rows(
        'SELECT * FROM ProductsF WHERE ProductsA = ? ORDER BY CAST(price AS INTEGER)',
        [(string)$cat['name']]
    );
    $rows = [];
    foreach ($items as $p) {
        if (p_ready($p) && p_enabled($p)) {
            $rows[] = [cb(
                p_icon($p) . ' ' . p_title($p) . ' — ' . money($p['price']) . (p_type($p) === 'boost' ? ' ت / هر بوست' : ' ت'),
                'buy,' . $p['id']
            )];
        }
    }
    if (!$rows) {
        screen($chat, $mid, '⛔ فعلا چیزی توی این بخش فعال نیست، بعدا سر بزن.', ik([[cb('◀️ بازگشت', 'my_bots')]]));
        return;
    }
    $rows[] = [cb('◀️ بازگشت', 'my_bots')];
    $d      = clean_desc($cat['Description']);
    screen(
        $chat,
        $mid,
        head('{e:bag}', h(Pe::strip((string)$cat['name']))) . ($d !== '' ? $d . "\n\n" : '')
        . "قیمت‌ها لحظه‌ای بروز می‌شن؛ گزینه‌ی دلخواهت رو انتخاب کن 👇",
        ik($rows)
    );
}

function cb_product(int $chat, int $uid, int $mid, int $pid): void
{
    sp_lazy();
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if (!$p || !p_ready($p) || !p_enabled($p)) {
        screen($chat, $mid, '⛔ این محصول وجود نداره یا فعلا غیرفعاله.', ik([[cb('◀️ بازگشت', 'my_bots')]]));
        return;
    }
    $cat  = Db::row('SELECT id FROM ProductsA WHERE name = ?', [(string)$p['ProductsA']]);
    $back = $cat ? 'hello,' . $cat['id'] : 'my_bots';
    $bal  = coin_of($uid);
    $need = p_type($p) === 'boost' ? (int)$p['price'] * boost_min() : (int)$p['price'];

    $t    = p_banner($p, $bal);
    $rows = [];
    if ($bal >= $need) {
        $rows[] = [cb('✅ ادامه خرید', 'ok,' . $pid)];
    } else {
        $t     .= "\n\n⚠️ موجودیت کافی نیست؛ <b>" . money($need - $bal) . '</b> تومان کم داری. اول حسابت رو شارژ کن 👇';
        $rows[] = [cb(BTN['topup'], 'add_coin')];
    }
    $rows[] = [cb('◀️ بازگشت', $back)];
    screen($chat, $mid, $t, ik($rows));
}

function cb_buy_start(int $chat, int $uid, int $pid): ?array
{
    sp_lazy();
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if (!$p || !p_ready($p) || !p_enabled($p)) {
        return ['❌ این محصول وجود نداره', true];
    }
    if (p_type($p) === 'boost') {
        if (coin_of($uid) < (int)$p['price'] * boost_min()) {
            return ['❌ موجودیت برای حداقل سفارش کافی نیست', true];
        }
        prompt(
            $chat,
            'boost_target,' . $pid,
            head('{e:boost}', h(p_title($p)))
            . "✍️ یوزرنیم یا لینک <b>کانال / گروه</b> رو بفرست\n"
            . "مثال: <code>@channel</code> یا <code>https://t.me/channel</code>\n\n"
            . "⚠️ کانال یا گروه باید در دسترس باشه و درست بودن آدرس با خودته."
        );
        return null;
    }
    if (coin_of($uid) < (int)$p['price']) {
        return ['❌ موجودیت کافی نیست', true];
    }
    prompt(
        $chat,
        'buy_account,' . $pid,
        head(p_icon($p), h(p_title($p)))
        . (p_type($p) === 'gift' ? '🎁 گیفتی که می‌فرستی: <b>' . p_qty($p) . "</b>\n" : '')
        . '💰 مبلغ قابل پرداخت: <b>' . money($p['price']) . "</b> تومان\n\n"
        . "✍️ یوزرنیم تلگرام گیرنده رو بفرست\nمثال: <code>@username</code>\n\n"
        . '⚠️ حواست باشه، درست بودن یوزرنیم با خودته.'
    );
    return null;
}

function cb_topup(int $chat, int $mid): void
{
    $s = Db::setting();
    if (($s['pay'] ?? 'on') !== 'on') {
        screen($chat, $mid, head('⛔', 'شارژ حساب') . 'فعلا شارژ حساب بسته است، کمی بعد دوباره امتحان کن 🙏', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return;
    }
    $rows = [];
    if (($s['idpay'] ?? '') === 'on' && trim((string)$s['idpay_merchant']) !== '') {
        $rows[] = [cb('🌐 درگاه پرداخت آنلاین', 'pay_idpay')];
    }
    if ((($s['ton'] ?? '') === 'on' && trim((string)$s['tonwalet']) !== '')
        || (($s['tron'] ?? '') === 'on' && trim((string)$s['tron_walet']) !== '')) {
        $rows[] = [cb('{e:usd} پرداخت با ارز دیجیتال', 'pay_crypto')];
    }
    if (($s['cart'] ?? '') === 'on' && trim((string)$s['cart_number']) !== '') {
        $rows[] = [cb('💳 کارت به کارت', 'pay_card')];
    }
    if (!$rows) {
        screen($chat, $mid, head('⛔', 'شارژ حساب') . 'فعلا هیچ روش پرداختی فعال نیست، بعدا سر بزن 🙏', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return;
    }
    $rows[] = [cb('🏠 منوی اصلی', 'home')];
    screen(
        $chat,
        $mid,
        head('💰', 'شارژ حساب')
        . '👛 موجودی فعلی: <b>' . money(coin_of($chat)) . "</b> تومان\n\n"
        . "هر روشی که برات راحت‌تره رو انتخاب کن، شارژ سریع انجام می‌شه ✨\n\n"
        . '👇 یکی از روش‌های زیر رو بزن',
        ik($rows)
    );
}

function cb_pay_crypto(int $chat, int $mid): void
{
    $s    = Db::setting();
    $rows = [];
    if (($s['tron'] ?? '') === 'on' && trim((string)$s['tron_walet']) !== '') {
        $rows[] = [cb('{e:trx} ترون (TRX)', 'pay_tron')];
    }
    if (($s['ton'] ?? '') === 'on' && trim((string)$s['tonwalet']) !== '') {
        $rows[] = [cb('{e:ton} گرام (TON)', 'pay_ton')];
    }
    if (!$rows) {
        screen($chat, $mid, 'فعلا پرداخت با ارز دیجیتال خاموشه.', ik([[cb('◀️ بازگشت', 'add_coin')]]));
        return;
    }
    $rows[] = [cb('◀️ بازگشت', 'add_coin')];
    screen($chat, $mid, head('{e:usd}', 'پرداخت با ارز دیجیتال') . "ارز موردنظرت رو انتخاب کن 👇\nبعد از واریز، حسابت خودکار شارژ می‌شه ✨", ik($rows));
}

function cb_pay_method(int $chat, string $method): ?array
{
    $s = Db::setting();
    if (($s['pay'] ?? 'on') !== 'on') {
        return ['شارژ حساب فعلا خاموشه', true];
    }
    switch ($method) {
        case 'idpay':
            if (($s['idpay'] ?? '') !== 'on' || trim((string)$s['idpay_merchant']) === '') {
                return ['درگاه پرداخت فعلا خاموشه', true];
            }
            prompt(
                $chat,
                'idpay_amount',
                head('🌐', 'پرداخت آنلاین')
                . "مبلغی که می‌خوای شارژ کنی رو به <b>تومان</b> بفرست ✍️\n\n"
                . '🔹 حداقل: <b>' . money(min_topup()) . "</b> تومان\n"
                . '🔹 حداکثر: <b>' . money(max_topup()) . '</b> تومان'
            );
            return null;
        case 'ton':
            if (($s['ton'] ?? '') !== 'on' || trim((string)$s['tonwalet']) === '') {
                return ['پرداخت با گرام (TON) فعلا خاموشه', true];
            }
            prompt(
                $chat,
                'crypto_ton',
                head('{e:ton}', 'واریز با گرام (TON)')
                . "گرام رو به آدرس زیر واریز کن:\n<code>" . h($s['tonwalet']) . "</code>\n\n"
                . "بعد از واریز، لینک تراکنش (از tonviewer.com یا tonscan.org) رو برام بفرست تا همون لحظه حسابت شارژ بشه ✨"
                . rate_note(rate_get('ton'), 'TON')
            );
            return null;
        case 'tron':
            if (($s['tron'] ?? '') !== 'on' || trim((string)$s['tron_walet']) === '') {
                return ['پرداخت با ترون فعلا خاموشه', true];
            }
            prompt(
                $chat,
                'crypto_tron',
                head('{e:trx}', 'واریز با ترون (TRX)')
                . "ترون رو به آدرس زیر واریز کن:\n<code>" . h($s['tron_walet']) . "</code>\n\n"
                . "بعد از واریز، لینک تراکنش (از tronscan.org) یا هش تراکنش رو برام بفرست تا همون لحظه حسابت شارژ بشه ✨"
                . rate_note(rate_get('trx'), 'TRX')
            );
            return null;
        case 'card':
            if (($s['cart'] ?? '') !== 'on' || trim((string)$s['cart_number']) === '') {
                return ['کارت به کارت فعلا خاموشه', true];
            }
            if (kyc_need($chat)) {
                kyc_notice($chat, 0, $chat);
                return null;
            }
            prompt($chat, 'card_receipt', card_text() . "\n\nمبلغ رو به کارت بالا واریز کن و بعد <b>عکس رسید</b> رو برام بفرست 🧾");
            return null;
    }
    return null;
}

/* ======================================================================
 *  Payment flows
 * ==================================================================== */

function pay_sig(int $uid, int $amount, int $t): string
{
    return substr(hash_hmac('sha256', "$uid|$amount|$t", Config::$token), 0, 24);
}

function step_idpay_amount(array $m): void
{
    $chat   = (int)$m['chat']['id'];
    $amount = parse_int((string)($m['text'] ?? ''));
    if ($amount === null) {
        Tg::send($chat, '✍️ فقط عدد بفرست، مثلا <code>200000</code>');
        return;
    }
    if ($amount < min_topup() || $amount > max_topup()) {
        Tg::send($chat, '⚠️ مبلغ باید بین <b>' . money(min_topup()) . '</b> تا <b>' . money(max_topup()) . '</b> تومان باشه');
        return;
    }
    if (kyc_need($chat)) {
        set_step($chat, 'none');
        drop_reply_kb($chat);
        kyc_notice($chat, 0, $chat);
        return;
    }
    $base = base_url();
    if ($base === '') {
        Tg::send($chat, '⚠️ یه مشکل فنی پیش اومد (آدرس سرور شناسایی نشد). لطفا به پشتیبانی خبر بده.');
        set_step($chat, 'none');
        return;
    }
    $t   = time();
    $url = $base . '/pay?' . http_build_query(['uid' => $chat, 'amount' => $amount, 't' => $t, 'sig' => pay_sig($chat, $amount, $t)]);
    set_step($chat, 'none');
    drop_reply_kb($chat);
    Tg::send(
        $chat,
        head('💳', 'درگاه پرداخت آماده‌ست')
        . '💰 مبلغ: <b>' . money($amount) . "</b> تومان\n\n"
        . "🔹 بعد از پرداخت، موجودیت خودکار شارژ می‌شه\n"
        . "🔹 اعتبار لینک: ۶۰ دقیقه\n\n"
        . '👇 برای پرداخت روی دکمه بزن',
        ik([[ub('💳 پرداخت ' . money($amount) . ' تومان', $url)], [cb('🏠 منوی اصلی', 'home')]])
    );
}

function tx_hash_hex(string $text): ?string
{
    if (preg_match('/\b([0-9a-fA-F]{64})\b/', $text, $mm)) {
        return strtolower($mm[1]);
    }
    if (preg_match('~(?:transaction|tx)/([A-Za-z0-9_\-+/]{43,44}={0,1})~', $text, $mm)) {
        $bin = base64_decode(strtr($mm[1], '-_', '+/'), true);
        if ($bin !== false && strlen($bin) === 32) {
            return bin2hex($bin);
        }
    }
    return null;
}

function ton_raw(string $a): ?string
{
    $a = trim($a);
    if (preg_match('/^(-?\d+):([0-9a-fA-F]{64})$/', $a, $mm)) {
        return $mm[1] . ':' . strtolower($mm[2]);
    }
    if (preg_match('/^[A-Za-z0-9_\-+\/=]{48}$/', $a)) {
        $bin = base64_decode(strtr($a, '-_', '+/'), true);
        if ($bin !== false && strlen($bin) === 36) {
            $wc = ord($bin[1]);
            if ($wc > 127) {
                $wc -= 256;
            }
            return $wc . ':' . bin2hex(substr($bin, 2, 32));
        }
    }
    return null;
}

function crypto_record(string $table, string $unit, int $uid, string $hash, float $amount, int $rate): void
{
    $credit = $rate > 0 ? (int)floor($amount * $rate) : 0;
    $result = $credit > 0 ? 'completed' : 'pending';
    $id     = Db::tx(function () use ($table, $uid, $hash, $amount, $credit, $result) {
        if (Db::val("SELECT 1 FROM `$table` WHERE hash = ?", [$hash]) !== null) {
            return null;
        }
        $new = (int)Db::val("SELECT COALESCE(MAX(CAST(id AS INTEGER)), 0) + 1 FROM `$table`");
        Db::exec(
            "INSERT INTO `$table` (id, user, tron, hash, time, date, result) VALUES (?,?,?,?,?,?,?)",
            [(string)$new, (string)$uid, sprintf('%.9F', $amount), $hash, Jalali::time(), Jalali::date(), $result]
        );
        if ($credit > 0) {
            coin_add($uid, $credit);
        }
        return $new;
    });

    if ($id === null) {
        Tg::send($uid, '⚠️ این تراکنش قبلاً ثبت شده است.');
        return;
    }

    $msg  = head('✅', 'پرداختت تایید شد!');
    $msg .= '💰 مبلغ: <b>' . rtrim(rtrim(sprintf('%.9F', $amount), '0'), '.') . " $unit</b>\n";
    $msg .= "🆔 شماره تراکنش: $id\n";
    $msg .= "🔗 هش: <code>$hash</code>\n";
    $msg .= '📅 تاریخ: ' . Jalali::date() . ' ' . Jalali::time() . "\n\n";
    $msg .= $credit > 0
        ? '🎉 <b>' . money($credit) . '</b> تومان به موجودیت اضافه شد، خرید خوبی داشته باشی!'
        : '⏳ تراکنشت ثبت شد و بعد از بررسی تیم، موجودیت شارژ می‌شه.';
    set_step($uid, 'none');
    drop_reply_kb($uid);
    Tg::send($uid, $msg, ik([[cb('🏠 منوی اصلی', 'home')]]));

    if ($credit === 0) {
        notify_admins(
            "🔔 <b>پرداخت کریپتو ثبت شد</b>\n\n👤 کاربر: <code>$uid</code>\n💰 مبلغ: "
            . rtrim(rtrim(sprintf('%.9F', $amount), '0'), '.') . " $unit\n🔗 <code>$hash</code>\n\nلطفاً موجودی کاربر را شارژ کنید.",
            ik([[cb('➕ شارژ کاربر', 'cc,' . $uid)]])
        );
    }
}

function step_crypto_ton(array $m): void
{
    $uid  = (int)$m['chat']['id'];
    $s    = Db::setting();
    $mine = ton_raw((string)$s['tonwalet']);
    if (!$mine) {
        Tg::send($uid, '❌ آدرس ولت تون توسط ادمین به‌درستی تنظیم نشده است.');
        return;
    }
    $hash = tx_hash_hex((string)($m['text'] ?? ''));
    if (!$hash) {
        Tg::send($uid, "❌ لطفاً یک لینک معتبر از TON Viewer یا TON Scan ارسال کنید.\nمثال:\n<code>https://tonviewer.com/transaction/5f5a3b8f9e2c4d1a8b7c9d6e5f4a3b2c1d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a</code>");
        return;
    }
    if (Db::val('SELECT 1 FROM ton_pays WHERE hash = ?', [$hash]) !== null) {
        Tg::send($uid, '⚠️ این تراکنش قبلاً ثبت شده است.');
        return;
    }
    $hdr = env('TONCENTER_API_KEY') !== '' ? ['X-API-Key: ' . env('TONCENTER_API_KEY')] : [];
    $r   = http_json('https://toncenter.com/api/v3/transactions?limit=1&hash=' . $hash, null, $hdr);
    if (!$r || $r['code'] !== 200 || !is_array($r['json'])) {
        Tg::send($uid, '❌ خطا در دریافت اطلاعات تراکنش. لطفاً چند دقیقه دیگر تلاش کنید.');
        return;
    }
    $tx = $r['json']['transactions'][0] ?? null;
    if (!is_array($tx)) {
        Tg::send($uid, '❌ تراکنش یافت نشد. چند دقیقه صبر کنید یا لینک را بررسی کنید.');
        return;
    }
    if (!empty($tx['description']['aborted'])) {
        Tg::send($uid, '❌ این تراکنش ناموفق بوده است.');
        return;
    }
    $dest = ton_raw((string)($tx['account'] ?? ($tx['in_msg']['destination'] ?? '')));
    $in   = $tx['in_msg'] ?? [];
    if ($dest !== $mine || empty($in['source'])) {
        Tg::send($uid, "❌ این تراکنش به ولت فروشگاه واریز نشده است.\nولت مورد نظر:\n<code>" . h($s['tonwalet']) . '</code>');
        return;
    }
    $amount = ((float)($in['value'] ?? 0)) / 1e9;
    if ($amount <= 0) {
        Tg::send($uid, '❌ مبلغ تراکنش صفر یا نامعتبر است.');
        return;
    }
    crypto_record('ton_pays', 'TON', $uid, $hash, $amount, rate_get('ton'));
}

function step_crypto_tron(array $m): void
{
    $uid    = (int)$m['chat']['id'];
    $s      = Db::setting();
    $wallet = trim((string)$s['tron_walet']);
    if ($wallet === '') {
        Tg::send($uid, '❌ آدرس ولت ترون توسط ادمین تنظیم نشده است.');
        return;
    }
    $hash = tx_hash_hex((string)($m['text'] ?? ''));
    if (!$hash) {
        Tg::send($uid, "❌ لطفاً یک لینک معتبر از ترون اسکن (Tronscan) یا هش تراکنش ارسال کنید.\nمثال:\n<code>https://tronscan.org/#/transaction/eb60adfccf98b9970163fa1e971ba9df0e549b181f732e2930a8c458fc2c7281</code>");
        return;
    }
    if (Db::val('SELECT 1 FROM tron_pays WHERE hash = ?', [$hash]) !== null) {
        Tg::send($uid, '⚠️ این تراکنش قبلاً ثبت شده است.');
        return;
    }
    $hdr = env('TRONGRID_API_KEY') !== '' ? ['TRON-PRO-API-KEY: ' . env('TRONGRID_API_KEY')] : [];
    $r   = http_json('https://api.trongrid.io/wallet/gettransactionbyid', ['value' => $hash, 'visible' => true], $hdr);
    if (!$r || $r['code'] !== 200 || !is_array($r['json'])) {
        Tg::send($uid, '❌ خطا در دریافت اطلاعات تراکنش. لطفاً چند دقیقه دیگر تلاش کنید.');
        return;
    }
    $tx = $r['json'];
    if (empty($tx['raw_data']['contract'][0])) {
        Tg::send($uid, '❌ تراکنش یافت نشد. لطفاً مطمئن شوید لینک صحیح است.');
        return;
    }
    $c = $tx['raw_data']['contract'][0];
    if (($c['type'] ?? '') !== 'TransferContract') {
        Tg::send($uid, '❌ فقط انتقال TRX پشتیبانی می‌شود.');
        return;
    }
    if (($tx['ret'][0]['contractRet'] ?? '') !== 'SUCCESS') {
        Tg::send($uid, '❌ تراکنش هنوز تایید نشده یا ناموفق است. کمی بعد دوباره تلاش کنید.');
        return;
    }
    $to = (string)($c['parameter']['value']['to_address'] ?? '');
    if ($to !== $wallet) {
        Tg::send($uid, "❌ این تراکنش به ولت فروشگاه واریز نشده است.\nولت مورد نظر:\n<code>" . h($wallet) . '</code>');
        return;
    }
    $amount = ((float)($c['parameter']['value']['amount'] ?? 0)) / 1e6;
    if ($amount <= 0) {
        Tg::send($uid, '❌ مبلغ تراکنش صفر یا نامعتبر است.');
        return;
    }
    crypto_record('tron_pays', 'TRX', $uid, $hash, $amount, rate_get('trx'));
}

function step_card_receipt(array $m): void
{
    $uid = (int)$m['chat']['id'];
    if (empty($m['photo']) || !is_array($m['photo'])) {
        Tg::send($uid, '🧾 لطفا فقط <b>عکس رسید</b> رو بفرست.');
        return;
    }
    $file = end($m['photo'])['file_id'];
    foreach (all_admins() as $a) {
        Tg::call('sendPhoto', [
            'chat_id'      => $a,
            'photo'        => $file,
            'parse_mode'   => 'HTML',
            'caption'      => "🧾 رسید واریزی کاربر : <code>$uid</code>\nبرای افزایش موجودی دکمه زیر را بزنید.",
            'reply_markup' => ik([[cb('➕ شارژ کاربر', 'cc,' . $uid)]]),
        ]);
    }
    set_step($uid, 'none');
    drop_reply_kb($uid);
    Tg::send($uid, head('✅', 'رسیدت دریافت شد') . "رسید برای تیم " . TEAM . " ارسال شد و بعد از بررسی، موجودیت شارژ می‌شه. ممنون از صبوریت 🙏", ik([[cb('🏠 منوی اصلی', 'home')]]));
}

function step_buy_account(array $m, string $arg): void
{
    $uid = (int)$m['chat']['id'];
    $txt = trim((string)($m['text'] ?? ''));
    sp_lazy();
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$arg]);
    if (!$p || !p_ready($p) || !p_enabled($p) || p_type($p) === 'boost') {
        set_step($uid, 'none');
        drop_reply_kb($uid);
        Tg::send($uid, '⛔ این محصول دیگه موجود نیست.', kb_main());
        return;
    }
    if (!preg_match('/^@?[A-Za-z][A-Za-z0-9_]{3,31}$/', $txt) && !preg_match('/^\d{5,15}$/', digits_en($txt))) {
        Tg::send($uid, "⚠️ یوزرنیم درست نیست.\nمثال: <code>@username</code>");
        return;
    }
    $account = preg_match('/^\d+$/', digits_en($txt)) ? digits_en($txt) : '@' . ltrim($txt, '@');
    $oid     = order_create($uid, $p, $account);
    if ($oid === null) {
        set_step($uid, 'none');
        drop_reply_kb($uid);
        Tg::send($uid, '⚠️ موجودیت کافی نیست، اول حسابت رو شارژ کن 👇', ik([[cb(BTN['topup'], 'add_coin')]]));
        return;
    }
    set_step($uid, 'none');
    drop_reply_kb($uid);
    Tg::send(
        $uid,
        head('✅', 'سفارشت ثبت شد!')
        . "🆔 شماره سفارش: <code>$oid</code>\n📦 " . h(p_title($p)) . "\n🎯 گیرنده: " . h($account)
        . "\n\n🛡 تیم " . TEAM . ' سفارشت رو بررسی می‌کنه و بعد از تایید، تحویل داده می‌شه. نتیجه همین‌جا بهت اطلاع داده می‌شه.',
        kb_main()
    );

    $t  = "🛎 <b>یک سفارش ثبت شد</b>\n\n";
    $t .= "🆔 سفارش: <code>$oid</code>\n";
    $t .= "👤 خریدار: <a href=\"tg://user?id=$uid\">$uid</a>\n";
    $t .= '🎯 اکانت گیرنده: ' . h($account) . "\n";
    $t .= '🔰 سرویس: ' . h(p_title($p)) . "\n";
    $t .= '🌐 مقدار: ' . p_qty($p) . "\n";
    $t .= '💰 مبلغ: ' . money($p['price']) . ' تومان';
    notify_admins($t, ik([
        [cb('✔️ تایید کردن', 'Compile,' . $oid)],
        [cb('✖️ رد کردن', 'notCompile,' . $oid)],
    ]));
}

function step_transfer_to(array $m): void
{
    $uid = (int)$m['chat']['id'];
    $to  = parse_int((string)($m['text'] ?? ''));
    if ($to === null || $to === $uid || !user_exists($to)) {
        Tg::send($uid, '⚠️ این آیدی درست نیست یا کاربر هنوز توی ربات عضو نشده.');
        return;
    }
    prompt($uid, 'transfer_amt,' . $to, '💸 مبلغ انتقال رو به تومان بفرست (حداقل ' . money(MIN_TRANSFER) . ').');
}

function step_transfer_amt(array $m, string $arg): void
{
    $uid = (int)$m['chat']['id'];
    $to  = (int)$arg;
    $amt = parse_int((string)($m['text'] ?? ''));
    if ($amt === null || $amt < MIN_TRANSFER) {
        Tg::send($uid, '⚠️ مبلغ درست نیست، حداقل ' . money(MIN_TRANSFER) . ' تومان.');
        return;
    }
    $ok = Db::tx(function () use ($uid, $to, $amt) {
        if (!user_exists($to) || !coin_sub($uid, $amt)) {
            return false;
        }
        coin_add($to, $amt);
        return true;
    });
    set_step($uid, 'none');
    drop_reply_kb($uid);
    if (!$ok) {
        Tg::send($uid, '⚠️ موجودیت کافی نیست.', kb_main());
        return;
    }
    Tg::send($uid, '✅ <b>' . money($amt) . "</b> تومان با موفقیت برای کاربر <code>$to</code> فرستاده شد.", kb_main());
    Tg::send($to, '💸 یه خبر خوب! <b>' . money($amt) . "</b> تومان از طرف کاربر <code>$uid</code> به حسابت اومد.");
}

function step_support(array $m): void
{
    $uid = (int)$m['chat']['id'];
    foreach (all_admins() as $a) {
        Tg::call('forwardMessage', ['chat_id' => $a, 'from_chat_id' => $uid, 'message_id' => $m['message_id']]);
        Tg::send($a, "👤 پیام از طرف کاربر : <code>$uid</code>", ik([[cb('↩️ پاسخ', 'reply,' . $uid)]]));
    }
    set_step($uid, 'none');
    drop_reply_kb($uid);
    Tg::send($uid, head('✅', 'پیامت رسید') . 'پیامت برای تیم پشتیبانی ' . TEAM . ' ارسال شد، به‌زودی جوابت رو می‌گیری 🙏', kb_main());
}

/* ======================================================================
 *  Admin: orders
 * ==================================================================== */

function admin_order(int $chat, int $mid, string $oid, bool $approve, int $adminId): ?array
{
    $o = Db::row('SELECT * FROM Orders WHERE id = ?', [$oid]);
    if (!$o) {
        return ['❌ سفارش یافت نشد!', true];
    }
    $newState = $approve ? 'compile' : 'NotCompile';
    $buyer    = (int)$o['user'];
    $changed  = Db::tx(function () use ($oid, $newState, $approve, $buyer, $o) {
        $n = Db::exec("UPDATE Orders SET result = ? WHERE id = ? AND result = 'Incomplete'", [$newState, $oid]);
        if ($n > 0 && !$approve) {
            coin_add($buyer, (int)$o['price']);
        }
        return $n;
    });
    if ($changed === 0) {
        $cur = Db::val('SELECT result FROM Orders WHERE id = ?', [$oid]);
        return ['⚠️ این سفارش قبلاً بررسی شده است: ' . status_label((string)$cur), true];
    }
    $p    = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$o['products_id']]);
    $name = $p ? p_title($p) : 'سرویس';

    if ($approve) {
        $promo = em_promo();
        Tg::send(
            $buyer,
            head('🎉', 'سفارشت تحویل داده شد!')
            . "🆔 شماره سفارش: <code>$oid</code>\n📦 " . h($name) . "\n📅 " . h($o['date']) . ' ' . h($o['time'])
            . "\n\nممنون که " . BRAND . ' رو انتخاب کردی، خوشحالیم که کنارتیم 🙏'
            . ($promo['text'] !== '' ? "\n\n" . HR . "\n" . $promo['text'] : ''),
            $promo['markup']
        );
    } else {
        Tg::send(
            $buyer,
            head('⚠️', 'سفارشت تایید نشد')
            . "متاسفانه این سفارش تایید نشد، ولی نگران نباش؛ مبلغش کامل به موجودیت برگشت.\n\n"
            . "🆔 شماره سفارش: <code>$oid</code>\n💰 مبلغ بازگشتی: <b>" . money($o['price']) . "</b> تومان\n\n"
            . 'اگه سوالی داشتی، پشتیبانی کنارته 🙏'
        );
    }
    if ($mid > 0) {
        Tg::call('editMessageReplyMarkup', [
            'chat_id'      => $chat,
            'message_id'   => $mid,
            'reply_markup' => ik([[cb(($approve ? '✅ تایید شد' : '❌ رد شد') . " (ادمین $adminId)", 'noop')]]),
        ]);
    }
    return [$approve ? '✅ سفارش تایید شد' : '✅ سفارش رد شد و مبلغ بازگشت داده شد', false];
}

/* ======================================================================
 *  Admin: panel actions
 * ==================================================================== */

function admin_stats(int $chat): void
{
    $users   = (int)Db::val('SELECT COUNT(*) FROM users');
    $banned  = (int)Db::val("SELECT COUNT(*) FROM users WHERE account = 'ban'");
    $today   = (int)Db::val('SELECT COUNT(*) FROM users WHERE date = ?', [Jalali::date()]);
    $balance = (int)Db::val('SELECT COALESCE(SUM(CAST(coin AS INTEGER)), 0) FROM users');
    $oAll    = (int)Db::val('SELECT COUNT(*) FROM Orders');
    $oWait   = (int)Db::val("SELECT COUNT(*) FROM Orders WHERE result = 'Incomplete'");
    $oDone   = (int)Db::val("SELECT COUNT(*) FROM Orders WHERE result = 'compile'");
    $oRej    = (int)Db::val("SELECT COUNT(*) FROM Orders WHERE result = 'NotCompile'");
    $sales   = (int)Db::val("SELECT COALESCE(SUM(CAST(price AS INTEGER)), 0) FROM Orders WHERE result = 'compile'");

    $t  = "📊 <b>آمار ربات</b>\n\n";
    $t .= "👥 کل کاربران: $users\n🆕 عضو امروز: $today\n⛔️ مسدود: $banned\n";
    $t .= '👛 مجموع موجودی کاربران: ' . money($balance) . " تومان\n\n";
    $t .= "🧾 سفارش‌ها: $oAll\n⏳ در انتظار: $oWait\n✅ تحویل‌شده: $oDone\n❌ ردشده: $oRej\n";
    $t .= '💰 مجموع فروش: ' . money($sales) . ' تومان';
    Tg::send($chat, $t, kb_panel());
}

function admin_check_user(int $chat, int $id): void
{
    $u = Db::row('SELECT * FROM users WHERE id = ?', [$id]);
    if (!$u) {
        Tg::send($chat, '❌ کاربری با این ایدی یافت نشد.');
        return;
    }
    $orders = (int)Db::val('SELECT COUNT(*) FROM Orders WHERE user = ?', [(string)$id]);
    $t  = "👤 <b>اطلاعات کاربر</b>\n\n🆔 ایدی: <code>$id</code>\n";
    $t .= '📅 عضویت: ' . h($u['date']) . ' ' . h($u['time']) . "\n";
    $t .= '💰 موجودی: ' . money($u['coin']) . " تومان\n";
    $t .= "📦 سفارش‌ها: $orders\n";
    $t .= '⚠️ وضعیت: ' . ($u['account'] === 'ban' ? 'بن شده' : 'فعال');
    admin_done($chat, $t);
}

function broadcast(int $chat, array $m, bool $forward): void
{
    @set_time_limit(0);
    $ids = Db::col("SELECT id FROM users WHERE account <> 'ban'");
    $ok  = 0;
    $bad = 0;
    Tg::send($chat, '⏳ در حال ارسال به ' . count($ids) . ' کاربر ...');
    foreach ($ids as $id) {
        $method = $forward ? 'forwardMessage' : 'copyMessage';
        $r      = Tg::call($method, ['chat_id' => $id, 'from_chat_id' => $chat, 'message_id' => $m['message_id']], 15);
        if ($r && !empty($r['ok'])) {
            $ok++;
        } elseif ($r && (int)($r['error_code'] ?? 0) === 429) {
            sleep((int)($r['parameters']['retry_after'] ?? 2) + 1);
            $r2 = Tg::call($method, ['chat_id' => $id, 'from_chat_id' => $chat, 'message_id' => $m['message_id']], 15);
            ($r2 && !empty($r2['ok'])) ? $ok++ : $bad++;
        } else {
            $bad++;
        }
        usleep(50000);
    }
    admin_done($chat, "✅ انجام شد\n\n📬 موفق: $ok\n⚠️ ناموفق: $bad");
}

function admin_button(string $text, int $chat): bool
{
    $map = array_flip(ADM);
    if (!isset($map[$text])) {
        return false;
    }
    switch ($map[$text]) {
        case 'stats':
            admin_stats($chat);
            break;
        case 'bc':
            prompt($chat, 'bc_send', '📝 پیام خود را بنویسید (متن، عکس، ویدیو و ... پشتیبانی می‌شود)');
            break;
        case 'fwd':
            prompt($chat, 'bc_fwd', '📝 پیام خود را فوروارد کنید');
            break;
        case 'svc':
            Tg::send($chat, '👤 جهت تنظیمات سرویس ها از دکمه های زیر استفاده کنید', ik([
                [cb('➕ سرویس اصلی', 'svc_add_org')],
                [cb('➕ سرویس فرعی', 'svc_add_sub')],
                [cb('➖ سرویس اصلی', 'svc_del_org')],
                [cb('➖ سرویس فرعی', 'svc_del_sub')],
            ]));
            break;
        case 'coin_add':
            prompt($chat, 'coin_add', "👤 ایدی عددی کاربر و مبلغ را با , بفرستید\n<code>id,amount</code>");
            break;
        case 'coin_sub':
            prompt($chat, 'coin_sub', "👤 ایدی عددی کاربر و مبلغ را با , بفرستید\n<code>id,amount</code>");
            break;
        case 'check':
            prompt($chat, 'check_user', '👤 ایدی عددی کاربر را ارسال کنید');
            break;
        case 'msg':
            prompt($chat, 'msg_user', "👤 ایدی عددی و پیام را به صورت زیر بنویسید\n<code>id,message</code>");
            break;
        case 'admins':
            adm_menu($chat, 0, $chat);
            break;
        case 'force_join':
            fj_menu($chat, 0);
            break;
        case 'gateway':
            gw_menu($chat, 0);
            break;
        case 'card':
            cd_menu($chat, 0);
            break;
        case 'tron':
            wl_menu($chat, 0, 'tron');
            break;
        case 'gram':
            wl_menu($chat, 0, 'ton');
            break;
        case 'rates':
            rt_menu($chat, 0);
            break;
        case 'stars_price':
            sp_menu($chat, 0);
            break;
        case 'profit':
            pm_menu($chat, 0);
            break;
        case 'gifts':
            gf_menu($chat, 0);
            break;
        case 'boost':
            bp_menu($chat, 0);
            break;
        case 'emoji':
            em_menu($chat, 0);
            break;
        case 'kyc':
            kya_menu($chat, 0);
            break;
        case 'bot_on':
            Db::setSetting('bot', 'on');
            Tg::send($chat, '✅ ربات با موفقیت روشن شد', kb_panel());
            break;
        case 'bot_off':
            Db::setSetting('bot', 'off');
            Tg::send($chat, '✅ ربات با موفقیت خاموش شد', kb_panel());
            break;
        case 'ban':
            prompt($chat, 'ban_user', '👤 ایدی عددی کاربر را ارسال کنید');
            break;
        case 'unban':
            prompt($chat, 'unban_user', '👤 ایدی عددی کاربر را ارسال کنید');
            break;
        case 'texts':
            Tg::send($chat, '👤 جهت تنظیم متن های ربات از دکمه های زیر استفاده کنید', ik([
                [cb('📩 متن استارت', 'set_start')],
                [cb('📩 متن راهنما', 'set_help')],
                [cb('📩 متن قوانین', 'set_rules')],
            ]));
            break;
        case 'settings':
            admin_settings_menu($chat, 0);
            break;
    }
    return true;
}

function mark($v): string
{
    return trim((string)$v) !== '' ? '✅' : '❌';
}

function admin_settings_menu(int $chat, int $mid): void
{
    $s  = Db::setting();
    $t  = "🤖 <b>تنظیمات ربات</b>\n\n";
    $t .= 'وضعیت ربات: ' . (($s['bot'] ?? 'on') === 'on' ? '🟢 روشن' : '🔴 خاموش') . "\n";
    $t .= 'درگاه ریالی (کلید API): ' . mark($s['idpay_merchant']) . "\n";
    $t .= 'کارت به کارت: ' . mark($s['cart_number']) . "\n";
    $t .= 'آدرس ترون: ' . mark($s['tron_walet']) . "\n";
    $t .= 'آدرس گرام (TON): ' . mark($s['tonwalet']) . "\n";
    $t .= 'قفل جوین اجباری: ' . (fj_enabled() ? '🟢' : '🔴') . ' (' . count(fj_list()) . " کانال)\n";
    $t .= 'قیمت خودکار استارز و پرمیوم: ' . (sp_enabled() ? '🟢 روشن' : '🔴 خاموش') . "\n";
    $t .= 'احراز هویت: ' . (kyc_on() ? '🟢 اجباری' : '🔴 غیرفعال') . "\n";
    $t .= 'کانال ایموجی پریمیوم: ' . mark(Db::kv('em_chan', '')) . "\n";
    $t .= 'آدرس سرور: ' . h(env_base_url() ?: '—');
    screen($chat, $mid, $t, ik([
        [cb('🌐 درگاه پرداخت', 'gw,menu'), cb('💳 کارت به کارت', 'cd,menu')],
        [cb('🪙 آدرس ترون', 'wl,tron,menu'), cb('💎 آدرس گرام', 'wl,ton,menu')],
        [cb('💱 نرخ ارز', 'rt,menu'), cb('⭐ قیمت استارز', 'sp,menu')],
        [cb('🎁 قیمت گیفت', 'gf,menu'), cb('🚀 قیمت بوست', 'bp,menu')],
        [cb('✨ کانال ایموجی', 'em,menu'), cb('🪪 احراز هویت', 'kya,menu')],
        [cb('📢 قفل جوین', 'fj,menu'), cb('👑 ادمین‌ها', 'adm,menu')],
        [cb('🔌 روش‌های شارژ', 'menu,shop'), cb('🧩 تنظیمات فروش', 'menu,pay')],
    ]));
}

function admin_toggle_menu(int $chat, int $mid, string $group): void
{
    if (!isset(TOGGLES[$group])) {
        return;
    }
    $rows = [];
    foreach (TOGGLES[$group]['items'] as $col => $label) {
        $rows[] = [cb((toggle_on($col) ? '🟢 ' : '🔴 ') . $label, 'tg,' . $col)];
    }
    $rows[] = [cb('◀️ بازگشت', 'menu,settings')];
    screen($chat, $mid, TOGGLES[$group]['title'] . "\n\n🟢 روشن  |  🔴 خاموش\nبرای تغییر وضعیت روی هر مورد بزنید.", ik($rows));
}

function admin_toggle(string $col): ?string
{
    foreach (TOGGLES as $group => $g) {
        if (isset($g['items'][$col])) {
            $next = toggle_on($col) ? 'off' : 'on';
            if (str_starts_with($col, 'k_')) {
                Db::kvSet($col, $next);
            } else {
                Db::setSetting($col, $next);
            }
            return $group;
        }
    }
    return null;
}

function admin_service_lists(int $chat, int $mid, string $kind): void
{
    $rows = [];
    if ($kind === 'org') {
        foreach (Db::rows('SELECT id, name FROM ProductsA ORDER BY rowid LIMIT 80') as $c) {
            $rows[] = [cb('🗑 ' . $c['name'], 'delA,' . $c['id'])];
        }
        $title = "🗑 <b>حذف سرویس اصلی</b>\n⚠️ زیرمجموعه‌های آن هم حذف می‌شوند.";
    } else {
        foreach (Db::rows('SELECT id, name, ProductsA FROM ProductsF ORDER BY rowid LIMIT 80') as $p) {
            $rows[] = [cb('🗑 ' . $p['name'] . ' (' . $p['ProductsA'] . ')', 'delF,' . $p['id'])];
        }
        $title = '🗑 <b>حذف سرویس فرعی</b>';
    }
    if (!$rows) {
        screen($chat, $mid, 'موردی برای حذف وجود ندارد.');
        return;
    }
    screen($chat, $mid, $title, ik($rows));
}

/* ======================================================================
 *  Admin: shared helpers
 * ==================================================================== */

function alert(string $text, bool $show = true): array
{
    return [mb_strlen($text) > 190 ? mb_substr($text, 0, 190) . '…' : $text, $show];
}

function is_main_admin(int $id): bool
{
    return in_array($id, Config::$admins, true);
}

function btn_back_settings(): array
{
    return [cb('◀️ تنظیمات', 'menu,settings')];
}

/* ======================================================================
 *  Admin: admins management
 * ==================================================================== */

function adm_menu(int $chat, int $mid, int $viewer): void
{
    $extra = array_values(array_filter(all_admins(), fn($a) => !is_main_admin($a)));
    $t     = "👑 <b>مدیریت ادمین‌ها</b>\n\nادمین‌های اصلی (متغیر ADMIN_ID):\n";
    foreach (Config::$admins as $a) {
        $t .= '• <a href="tg://user?id=' . $a . '">' . $a . "</a> 👑\n";
    }
    $t .= "\nادمین‌های اضافه‌شده:\n";
    if ($extra) {
        foreach ($extra as $a) {
            $t .= '• <a href="tg://user?id=' . $a . '">' . $a . "</a>\n";
        }
    } else {
        $t .= "—\n";
    }
    $rows = [];
    if (is_main_admin($viewer)) {
        $t     .= "\nℹ️ ادمین جدید به پنل مدیریت، سفارش‌ها و پیام‌های پشتیبانی دسترسی کامل دارد. ادمین‌های اضافه‌شده نمی‌توانند ادمین جدید اضافه یا حذف کنند.";
        $rows[] = [cb('➕ افزودن ادمین جدید', 'adm,add')];
        foreach ($extra as $a) {
            $rows[] = [cb('🗑 حذف ادمین ' . $a, 'adm,del,' . $a)];
        }
    } else {
        $t .= "\n⚠️ فقط ادمین اصلی می‌تواند ادمین اضافه یا حذف کند.";
    }
    $rows[] = btn_back_settings();
    screen($chat, $mid, $t, ik($rows));
}

function adm_action(int $chat, int $mid, int $viewer, string $sub, string $arg): ?array
{
    if ($sub === 'menu' || $sub === 'cancel') {
        adm_menu($chat, $mid, $viewer);
        return null;
    }
    if (!is_main_admin($viewer)) {
        return alert('⛔️ فقط ادمین اصلی می‌تواند این کار را انجام دهد');
    }
    $id = (int)$arg;
    switch ($sub) {
        case 'add':
            prompt(
                $chat,
                'adm_add',
                "👑 <b>افزودن ادمین جدید</b>\n\nیکی از روش‌های زیر را انجام دهید:\n"
                . "• آیدی عددی کاربر را بفرستید (مثلا <code>123456789</code>)\n"
                . "• یا یک پیام از کاربر را اینجا فوروارد کنید\n\n"
                . "⚠️ کاربر باید قبلا ربات را /start کرده باشد.\n"
                . "💡 آیدی عددی را از ربات @userinfobot می‌توان گرفت."
            );
            break;
        case 'addok':
            if ($id <= 0) {
                return alert('❌ آیدی نامعتبر');
            }
            if (!is_admin($id)) {
                Db::exec('INSERT INTO admin (id) VALUES (?)', [(string)$id]);
            }
            $sent = Tg::send(
                $id,
                "🎉 <b>تبریک!</b>\nشما توسط مدیریت به‌عنوان <b>ادمین</b> ربات انتخاب شدید.\n\nبرای باز کردن پنل مدیریت دستور /admin را بفرستید یا از دکمه‌های زیر استفاده کنید.",
                kb_panel()
            );
            adm_menu($chat, $mid, $viewer);
            return alert($sent ? '✅ ادمین با موفقیت اضافه شد' : '✅ اضافه شد، اما پیام به کاربر ارسال نشد', false);
        case 'del':
            screen(
                $chat,
                $mid,
                "⚠️ آیا از حذف ادمین <code>$id</code> مطمئن هستید؟",
                ik([[cb('✅ بله، حذف شود', 'adm,delok,' . $id), cb('❌ انصراف', 'adm,cancel')]])
            );
            break;
        case 'delok':
            if (is_main_admin($id)) {
                return alert('⛔️ ادمین اصلی قابل حذف نیست');
            }
            Db::exec('DELETE FROM admin WHERE id = ?', [(string)$id]);
            Tg::send($id, 'ℹ️ دسترسی ادمین شما از ربات برداشته شد.', ['remove_keyboard' => true]);
            adm_menu($chat, $mid, $viewer);
            return alert('✅ ادمین حذف شد', false);
    }
    return null;
}

function step_adm_add(int $chat, array $m): void
{
    if (!is_main_admin($chat)) {
        set_step($chat, 'none');
        Tg::send($chat, '⛔️ فقط ادمین اصلی می‌تواند ادمین اضافه کند.', kb_panel());
        return;
    }
    $id = null;
    $o  = $m['forward_origin'] ?? null;
    if (is_array($o) && ($o['type'] ?? '') === 'hidden_user') {
        Tg::send($chat, "❌ این کاربر فوروارد خود را مخفی کرده است.\nلطفا آیدی عددی او را به‌صورت متن بفرستید.");
        return;
    }
    if (is_array($o) && ($o['type'] ?? '') === 'user' && isset($o['sender_user']['id'])) {
        $id = (int)$o['sender_user']['id'];
    } elseif (!empty($m['forward_from']['id'])) {
        $id = (int)$m['forward_from']['id'];
    } elseif (!empty($m['contact']['user_id'])) {
        $id = (int)$m['contact']['user_id'];
    } else {
        $id = parse_int((string)($m['text'] ?? ''));
    }
    if ($id === null || $id <= 0) {
        Tg::send($chat, '❌ آیدی عددی نامعتبر است. فقط عدد بفرستید یا یک پیام از کاربر فوروارد کنید.');
        return;
    }
    if (is_admin($id)) {
        Tg::send($chat, '⚠️ این کاربر هم‌اکنون ادمین است.');
        return;
    }
    $info = Tg::call('getChat', ['chat_id' => $id], 10);
    if (!user_exists($id) && !($info && !empty($info['ok']))) {
        Tg::send($chat, "❌ این کاربر پیدا نشد.\nاز او بخواهید ابتدا ربات را /start کند، سپس دوباره آیدی را بفرستید.");
        return;
    }
    $r    = $info['result'] ?? [];
    $name = trim((string)($r['first_name'] ?? '') . ' ' . (string)($r['last_name'] ?? ''));
    $un   = !empty($r['username']) ? '@' . $r['username'] : '—';
    set_step($chat, 'none');
    Tg::send($chat, '🔎 کاربر پیدا شد.', kb_panel());
    Tg::send(
        $chat,
        "👤 <b>تایید افزودن ادمین</b>\n\n🆔 آیدی: <code>$id</code>\n📛 نام: " . h($name !== '' ? $name : '—') . "\n🔗 یوزرنیم: " . h($un)
        . "\n\nاین کاربر ادمین شود؟",
        ik([[cb('✅ تایید و افزودن', 'adm,addok,' . $id), cb('❌ انصراف', 'adm,cancel')]])
    );
}

/* ======================================================================
 *  Admin: forced join
 * ==================================================================== */

function fj_menu(int $chat, int $mid): void
{
    $list = fj_list();
    $on   = fj_enabled();
    $t    = "📢 <b>قفل جوین اجباری</b>\n\n";
    $t   .= 'وضعیت: ' . ($on ? '🟢 فعال' : '🔴 غیرفعال') . "\n";
    $t   .= 'کانال‌ها: ' . count($list) . '/' . FJ_MAX . "\n\n";
    if ($list) {
        foreach ($list as $i => $c) {
            $t .= ($i + 1) . '. ' . h($c['title']) . ' — <code>' . h($c['id']) . "</code>\n";
        }
    } else {
        $t .= "هنوز کانالی اضافه نشده است.\n";
    }
    $t .= "\nℹ️ کاربران قبل از استفاده از ربات باید عضو همه کانال‌های بالا باشند. ربات باید در هر کانال <b>ادمین</b> باشد. ادمین‌ها مستثنی هستند.";

    $rows   = [];
    $rows[] = [cb($on ? '🔴 غیرفعال کردن قفل' : '🟢 فعال کردن قفل', 'fj,tog')];
    $rows[] = [cb('➕ افزودن کانال', 'fj,add')];
    foreach ($list as $c) {
        $rows[] = [cb('🗑 حذف: ' . $c['title'], 'fj,del,' . fj_key($c['id']))];
    }
    $rows[] = [cb('🔍 بررسی وضعیت کانال‌ها', 'fj,chk')];
    $rows[] = btn_back_settings();
    screen($chat, $mid, $t, ik($rows));
}

function fj_check(int $chat, int $mid): void
{
    $t = "🔍 <b>بررسی وضعیت کانال‌ها</b>\n\n";
    $list = fj_list();
    if (!$list) {
        $t .= 'کانالی ثبت نشده است.';
    }
    foreach ($list as $c) {
        $r  = Tg::call('getChatMember', ['chat_id' => fj_chat_id($c['id']), 'user_id' => bot_id()], 10);
        $st = $r['result']['status'] ?? '';
        $ok = in_array($st, ['administrator', 'creator'], true);
        $t .= ($ok ? '✅ ' : '❌ ') . h($c['title']) . ($ok
            ? " — ربات ادمین است\n"
            : " — ربات ادمین نیست یا دسترسی ندارد (قفل این کانال اعمال نمی‌شود)\n");
    }
    screen($chat, $mid, $t, ik([[cb('◀️ بازگشت', 'fj,menu')]]));
}

function fj_action(int $chat, int $mid, string $sub, string $arg): ?array
{
    switch ($sub) {
        case 'menu':
            fj_menu($chat, $mid);
            break;
        case 'tog':
            if (!fj_enabled() && !fj_list()) {
                return alert('ابتدا حداقل یک کانال اضافه کنید');
            }
            Db::kvSet('fj_on', fj_enabled() ? 'off' : 'on');
            fj_menu($chat, $mid);
            break;
        case 'add':
            if (count(fj_list()) >= FJ_MAX) {
                return alert('حداکثر ' . FJ_MAX . ' کانال مجاز است');
            }
            prompt(
                $chat,
                'fj_add',
                "📢 <b>افزودن کانال به قفل جوین</b>\n\n"
                . "🔹 ابتدا ربات را به کانال اضافه و <b>ادمین</b> کنید.\n"
                . "🔹 سپس یکی از این‌ها را اینجا بفرستید:\n"
                . "• یوزرنیم کانال: <code>@mychannel</code>\n"
                . "• لینک کانال: <code>https://t.me/mychannel</code>\n"
                . "• برای کانال خصوصی: یک پست از کانال را به همین چت فوروارد کنید.\n\n"
                . "ربات خودش ادمین بودن را بررسی و لینک عضویت را آماده می‌کند."
            );
            break;
        case 'del':
            foreach (fj_list() as $c) {
                if (fj_key($c['id']) === $arg) {
                    screen(
                        $chat,
                        $mid,
                        '⚠️ کانال «' . h($c['title']) . '» از قفل جوین حذف شود؟',
                        ik([[cb('✅ بله، حذف شود', 'fj,delok,' . $arg), cb('❌ انصراف', 'fj,menu')]])
                    );
                    return null;
                }
            }
            return alert('کانال پیدا نشد');
        case 'delok':
            $list = array_values(array_filter(fj_list(), fn($c) => fj_key($c['id']) !== $arg));
            fj_save($list);
            if (!$list) {
                Db::kvSet('fj_on', 'off');
            }
            fj_menu($chat, $mid);
            return alert('✅ کانال حذف شد', false);
        case 'chk':
            fj_check($chat, $mid);
            break;
    }
    return null;
}

function fj_parse_target(array $m): ?string
{
    $o = $m['forward_origin'] ?? null;
    if (is_array($o) && isset($o['chat']['id']) && in_array($o['type'] ?? '', ['channel', 'chat'], true)) {
        return (string)$o['chat']['id'];
    }
    if (is_array($o) && isset($o['sender_chat']['id'])) {
        return (string)$o['sender_chat']['id'];
    }
    if (!empty($m['forward_from_chat']['id'])) {
        return (string)$m['forward_from_chat']['id'];
    }
    $t = trim((string)($m['text'] ?? ''));
    if (preg_match('~^-100\d{5,}$~', $t)) {
        return $t;
    }
    if (preg_match('~^(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z][A-Za-z0-9_]{3,31})/?(?:\d+)?$~i', $t, $mm)) {
        return '@' . $mm[1];
    }
    if (preg_match('~^@?([A-Za-z][A-Za-z0-9_]{3,31})$~', $t, $mm)) {
        return '@' . $mm[1];
    }
    return null;
}

function step_fj_add(int $chat, array $m): void
{
    $target = fj_parse_target($m);
    if ($target === null) {
        Tg::send(
            $chat,
            "❌ ورودی نامعتبر است.\n\nیکی از این‌ها را بفرستید:\n• <code>@mychannel</code>\n• <code>https://t.me/mychannel</code>\n• فوروارد یک پست از کانال (برای کانال خصوصی)"
        );
        return;
    }
    $info = Tg::call('getChat', ['chat_id' => fj_chat_id($target)], 10);
    if (!$info || empty($info['ok'])) {
        Tg::send($chat, "❌ کانال پیدا نشد.\nمطمئن شوید یوزرنیم درست است و ربات در کانال عضو و ادمین شده است، سپس دوباره بفرستید.");
        return;
    }
    $c = $info['result'];
    if (!in_array($c['type'] ?? '', ['channel', 'supergroup', 'group'], true)) {
        Tg::send($chat, '❌ فقط کانال یا گروه قابل قبول است.');
        return;
    }
    $cid = (string)$c['id'];
    foreach (fj_list() as $x) {
        if ($x['id'] === $cid) {
            Tg::send($chat, '⚠️ این کانال قبلا اضافه شده است.');
            return;
        }
    }
    if (count(fj_list()) >= FJ_MAX) {
        admin_done($chat, '❌ حداکثر ' . FJ_MAX . ' کانال مجاز است.');
        return;
    }
    $me = Tg::call('getChatMember', ['chat_id' => $c['id'], 'user_id' => bot_id()], 10);
    $st = $me['result']['status'] ?? '';
    if (!in_array($st, ['administrator', 'creator'], true)) {
        Tg::send(
            $chat,
            "❌ ربات در این کانال <b>ادمین</b> نیست.\n\nراهنما:\n🔹 وارد کانال شوید ← مدیران ← افزودن مدیر\n🔹 ربات را اضافه کنید (دسترسی «دعوت کاربران» را فعال بگذارید)\n🔹 دوباره همین پیام را بفرستید."
        );
        return;
    }
    $title = (string)($c['title'] ?? $target);
    if (!empty($c['username'])) {
        $link = 'https://t.me/' . $c['username'];
    } else {
        $e    = Tg::call('exportChatInviteLink', ['chat_id' => $c['id']], 10);
        $link = (string)($e['result'] ?? '');
        if ($link === '') {
            Tg::send($chat, "❌ این کانال خصوصی است و ربات اجازهٔ ساخت لینک دعوت ندارد.\nدسترسی «دعوت کاربران از طریق لینک» را برای ربات فعال کنید و دوباره بفرستید.");
            return;
        }
    }
    $list   = fj_list();
    $list[] = ['id' => $cid, 'title' => $title, 'link' => $link];
    fj_save($list);
    Db::kvSet('fj_on', 'on');
    admin_done($chat, '✅ کانال «' . h($title) . "» به قفل جوین اضافه شد و قفل فعال است.\nاز این پس کاربران باید عضو این کانال باشند.");
    fj_menu($chat, 0);
}

/* ======================================================================
 *  Admin: IDPay gateway
 * ==================================================================== */

function min_topup(): int
{
    return max(1000, (int)Db::kv('min_topup', (string)DEF_MIN_TOPUP));
}

function max_topup(): int
{
    $v = (int)Db::kv('max_topup', (string)DEF_MAX_TOPUP);
    return $v >= min_topup() ? $v : DEF_MAX_TOPUP;
}

function idpay_sandbox(): bool
{
    return Db::kv('idpay_sandbox', '0') === '1';
}

function gw_mask(string $k): string
{
    $n = strlen($k);
    return $n <= 8 ? str_repeat('•', $n) : substr($k, 0, 4) . str_repeat('•', 8) . substr($k, -4);
}

function idpay_test(): array
{
    $key = trim((string)(Db::setting()['idpay_merchant'] ?? ''));
    if ($key === '') {
        return [false, 'کلید API ثبت نشده است.'];
    }
    $base = base_url();
    if ($base === '') {
        return [false, 'آدرس سرور مشخص نیست؛ در Railway دامنه (Generate Domain) بسازید.'];
    }
    $r = http_json('https://api.idpay.ir/v1.1/payment', [
        'order_id' => 'test-' . time(),
        'amount'   => 10000,
        'desc'     => 'test connection',
        'callback' => $base . '/pay/back',
    ], ['X-API-KEY: ' . $key, 'X-SANDBOX: ' . (idpay_sandbox() ? '1' : '0')]);
    $j = $r['json'] ?? null;
    if (!$r || !is_array($j)) {
        return [false, 'ارتباط با سرور ایدی پی برقرار نشد.'];
    }
    if (!empty($j['id']) || !empty($j['link'])) {
        return [true, 'اتصال به درگاه برقرار است و کلید معتبر است.'];
    }
    $code = (int)($j['error_code'] ?? ($j['error']['code'] ?? 0));
    $map  = [
        11 => 'کاربر مسدود شده است',
        12 => 'کلید API یافت نشد (کلید را بررسی کنید)',
        13 => 'درخواست از IP نامعتبر ارسال شده است',
        14 => 'وب‌سرویس شما در حال بررسی است یا تایید نشده',
        21 => 'حساب بانکی متصل به وب‌سرویس تایید نشده است',
        22 => 'وب‌سرویس یافت نشد',
        23 => 'اعتبارسنجی وب‌سرویس ناموفق بود',
        24 => 'حساب بانکی مرتبط با وب‌سرویس غیرفعال است',
        38 => 'دامنهٔ آدرس بازگشت با دامنهٔ ثبت‌شده در وب‌سرویس ایدی پی همخوانی ندارد',
        39 => 'آدرس بازگشت نامعتبر است',
    ];
    $msg = $map[$code] ?? (string)($j['error_message'] ?? ($j['error']['message'] ?? 'خطای نامشخص'));
    return [false, "خطا (کد $code): $msg"];
}

function gw_menu(int $chat, int $mid): void
{
    $s    = Db::setting();
    $key  = trim((string)($s['idpay_merchant'] ?? ''));
    $on   = ($s['idpay'] ?? 'on') === 'on';
    $base = base_url();
    $host = $base !== '' ? (string)parse_url($base, PHP_URL_HOST) : '';

    $t  = "🌐 <b>درگاه پرداخت ریالی (IDPay)</b>\n\n";
    $t .= 'وضعیت: ' . ($key === '' ? '⚪️ نیاز به ثبت کلید API' : ($on ? '🟢 فعال و در دسترس کاربران' : '🔴 غیرفعال')) . "\n";
    $t .= 'کلید API: ' . ($key !== '' ? '✅ <code>' . h(gw_mask($key)) . '</code>' : '❌ ثبت نشده') . "\n";
    $t .= 'حالت: ' . (idpay_sandbox() ? '🧪 آزمایشی (Sandbox) — پرداخت واقعی انجام نمی‌شود' : '🚀 واقعی') . "\n";
    $t .= 'حداقل مبلغ: ' . money(min_topup()) . " تومان\n";
    $t .= 'حداکثر مبلغ: ' . money(max_topup()) . " تومان\n";
    $t .= 'آدرس بازگشت (Callback): ' . ($base !== '' ? '<code>' . h($base . '/pay/back') . '</code>' : '⚠️ نامشخص') . "\n\n";
    $t .= "📌 <b>راه‌اندازی:</b>\n"
        . "🔹 در idpay.ir وب‌سرویس بسازید" . ($host !== '' ? " و دامنهٔ <code>" . h($host) . "</code> را ثبت کنید" : '') . ".\n"
        . "🔹 «کلید API» را با دکمهٔ زیر در ربات ثبت کنید.\n"
        . "🔹 با «تست اتصال» از درست بودن همه چیز مطمئن شوید.\n"
        . '🔹 برای پرداخت واقعی، حالت آزمایشی را خاموش کنید.';

    screen($chat, $mid, $t, ik([
        [cb('🔑 ' . ($key !== '' ? 'تغییر' : 'ثبت') . ' کلید API', 'gw,key')],
        [cb($on ? '🔴 غیرفعال کردن درگاه' : '🟢 فعال کردن درگاه', 'gw,tog'), cb(idpay_sandbox() ? '🚀 رفتن به حالت واقعی' : '🧪 رفتن به حالت آزمایشی', 'gw,sbx')],
        [cb('⬇️ حداقل مبلغ', 'gw,min'), cb('⬆️ حداکثر مبلغ', 'gw,max')],
        [cb('🔍 تست اتصال درگاه', 'gw,test')],
        btn_back_settings(),
    ]));
}

function gw_action(int $chat, int $mid, string $sub): ?array
{
    $s = Db::setting();
    switch ($sub) {
        case 'menu':
            gw_menu($chat, $mid);
            break;
        case 'key':
            prompt(
                $chat,
                'gw_key',
                "🔑 <b>کلید API ایدی پی</b> را ارسال کنید.\n\nمثال: <code>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</code>\n\n🔒 برای امنیت، پیام شما بعد از ذخیره حذف می‌شود."
            );
            break;
        case 'tog':
            if (trim((string)($s['idpay_merchant'] ?? '')) === '') {
                return alert('ابتدا کلید API را ثبت کنید');
            }
            Db::setSetting('idpay', ($s['idpay'] ?? 'on') === 'on' ? 'off' : 'on');
            gw_menu($chat, $mid);
            break;
        case 'sbx':
            Db::kvSet('idpay_sandbox', idpay_sandbox() ? '0' : '1');
            gw_menu($chat, $mid);
            return alert(idpay_sandbox() ? '🧪 حالت آزمایشی فعال شد' : '🚀 حالت واقعی فعال شد', false);
        case 'min':
            prompt($chat, 'gw_min', '⬇️ حداقل مبلغ شارژ را به تومان ارسال کنید (حداقل ۱,۰۰۰).' . "\nمقدار فعلی: " . money(min_topup()));
            break;
        case 'max':
            prompt($chat, 'gw_max', '⬆️ حداکثر مبلغ شارژ را به تومان ارسال کنید (حداکثر ۵۰,۰۰۰,۰۰۰).' . "\nمقدار فعلی: " . money(max_topup()));
            break;
        case 'test':
            [$ok, $msg] = idpay_test();
            return alert(($ok ? '✅ ' : '❌ ') . $msg);
    }
    return null;
}

function step_gw_key(int $chat, array $m): void
{
    $text = trim((string)($m['text'] ?? ''));
    if (!preg_match('/^[A-Za-z0-9_\-]{16,80}$/', $text)) {
        Tg::send($chat, "❌ کلید نامعتبر است.\nکلید API ایدی پی معمولا یک کد مثل <code>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</code> است.");
        return;
    }
    if (isset($m['message_id'])) {
        Tg::delete($chat, (int)$m['message_id']);
    }
    Db::setSetting('idpay_merchant', $text);
    Db::setSetting('idpay', 'on');
    [$ok, $msg] = idpay_test();
    admin_done($chat, "✅ کلید API ذخیره شد و برای امنیت پیام شما حذف شد.\n\n" . ($ok ? '✅ ' : '⚠️ ') . h($msg));
    gw_menu($chat, 0);
}

function step_gw_limit(int $chat, string $name, string $text): void
{
    $n = parse_int($text);
    if ($n === null) {
        Tg::send($chat, '❌ فقط عدد (به تومان) ارسال کنید.');
        return;
    }
    if ($name === 'gw_min') {
        if ($n < 1000 || $n > max_topup()) {
            Tg::send($chat, '❌ حداقل باید بین ۱,۰۰۰ تا حداکثر فعلی (' . money(max_topup()) . ') باشد.');
            return;
        }
        Db::kvSet('min_topup', (string)$n);
    } else {
        if ($n < min_topup() || $n > 50000000) {
            Tg::send($chat, '❌ حداکثر باید بین حداقل فعلی (' . money(min_topup()) . ') تا ۵۰,۰۰۰,۰۰۰ باشد.');
            return;
        }
        Db::kvSet('max_topup', (string)$n);
    }
    admin_done($chat, '✅ ذخیره شد.');
    gw_menu($chat, 0);
}

/* ======================================================================
 *  Admin: card to card
 * ==================================================================== */

function card_bank(string $d): string
{
    static $bins = [
        '603799' => 'ملی', '589210' => 'سپه', '627648' => 'توسعه صادرات', '627353' => 'تجارت', '585983' => 'تجارت',
        '610433' => 'ملت', '621986' => 'سامان', '639346' => 'سینا', '502229' => 'پاسارگاد', '639607' => 'سرمایه',
        '622106' => 'پارسیان', '627412' => 'اقتصاد نوین', '603769' => 'صادرات', '627961' => 'صنعت و معدن',
        '603770' => 'کشاورزی', '639217' => 'کشاورزی', '589463' => 'رفاه', '636214' => 'آینده', '502938' => 'دی',
        '504706' => 'شهر', '502806' => 'شهر', '628023' => 'مسکن', '505785' => 'ایران زمین', '636949' => 'حکمت ایرانیان',
        '627760' => 'پست بانک', '606373' => 'قرض‌الحسنه مهر ایران', '627488' => 'کارآفرین', '636795' => 'مرکزی',
    ];
    return $bins[substr($d, 0, 6)] ?? '';
}

function card_text(): string
{
    $raw  = trim((string)(Db::setting()['cart_number'] ?? ''));
    $norm = digits_en($raw);
    $d    = preg_replace('/\D+/', '', $norm) ?? '';
    $name = trim(Db::kv('card_holder', ''));
    if (strlen($d) === 16 && preg_match('/^[\d\s\-]+$/', $norm)) {
        $t = "💳 <b>اطلاعات کارت</b>\n\n🔢 شماره کارت:\n<code>$d</code>\n" . trim(chunk_split($d, 4, ' ')) . "\n";
        if ($name !== '') {
            $t .= '👤 به نام: <b>' . h($name) . "</b>\n";
        }
        $bank = card_bank($d);
        if ($bank !== '') {
            $t .= '🏦 بانک: ' . $bank . "\n";
        }
        return rtrim($t);
    }
    return '💳 ' . h($raw) . ($name !== '' ? "\n👤 به نام: <b>" . h($name) . '</b>' : '');
}

function cd_menu(int $chat, int $mid): void
{
    $s    = Db::setting();
    $has  = trim((string)($s['cart_number'] ?? '')) !== '';
    $on   = ($s['cart'] ?? 'on') === 'on';
    $t    = "💳 <b>کارت به کارت</b>\n\n";
    $t   .= 'وضعیت: ' . (!$has ? '⚪️ نیاز به ثبت کارت' : ($on ? '🟢 فعال' : '🔴 غیرفعال')) . "\n\n";
    $t   .= $has ? "کاربران این متن را هنگام پرداخت می‌بینند:\n\n" . card_text() : 'هنوز کارتی ثبت نشده است.';
    $rows = [[cb('✏️ ' . ($has ? 'تغییر' : 'ثبت') . ' اطلاعات کارت', 'cd,set')]];
    if ($has) {
        $rows[] = [cb($on ? '🔴 غیرفعال کردن' : '🟢 فعال کردن', 'cd,tog'), cb('🗑 حذف کارت', 'cd,del')];
    }
    $rows[] = btn_back_settings();
    screen($chat, $mid, $t, ik($rows));
}

function cd_action(int $chat, int $mid, string $sub): ?array
{
    $s = Db::setting();
    switch ($sub) {
        case 'menu':
            cd_menu($chat, $mid);
            break;
        case 'set':
            prompt($chat, 'card_num', "💳 <b>مرحله ۱ از ۲</b>\n\nشماره کارت ۱۶ رقمی را ارسال کنید.\nمثال: <code>6037991123456789</code>");
            break;
        case 'tog':
            if (trim((string)($s['cart_number'] ?? '')) === '') {
                return alert('ابتدا اطلاعات کارت را ثبت کنید');
            }
            Db::setSetting('cart', ($s['cart'] ?? 'on') === 'on' ? 'off' : 'on');
            cd_menu($chat, $mid);
            break;
        case 'del':
            screen($chat, $mid, '⚠️ اطلاعات کارت حذف شود؟', ik([[cb('✅ بله، حذف شود', 'cd,delok'), cb('❌ انصراف', 'cd,menu')]]));
            break;
        case 'delok':
            Db::setSetting('cart_number', '');
            Db::kvSet('card_holder', '');
            cd_menu($chat, $mid);
            return alert('✅ کارت حذف شد', false);
    }
    return null;
}

function step_card_num(int $chat, string $text): void
{
    $d = preg_replace('/\D+/', '', digits_en($text)) ?? '';
    if (strlen($d) !== 16) {
        Tg::send($chat, '❌ شماره کارت باید دقیقا ۱۶ رقم باشد. دوباره ارسال کنید.');
        return;
    }
    if (!luhn_ok($d)) {
        Tg::send($chat, '❌ این شماره کارت معتبر نیست (رقم کنترلی اشتباه است). دوباره بررسی و ارسال کنید.');
        return;
    }
    $bank = card_bank($d);
    prompt(
        $chat,
        'card_name,' . $d,
        "✅ شماره کارت: <code>$d</code>" . ($bank !== '' ? "\n🏦 بانک: $bank" : '')
        . "\n\n👤 <b>مرحله ۲ از ۲</b>\nنام و نام خانوادگی صاحب کارت را ارسال کنید.\nمثال: <code>علی رضایی</code>"
    );
}

function step_card_name(int $chat, string $digits, string $text): void
{
    $name = trim(preg_replace('/\s+/u', ' ', $text) ?? '');
    if (!preg_match('/^\d{16}$/', $digits)) {
        set_step($chat, 'none');
        Tg::send($chat, '❌ مرحله منقضی شد. دوباره از اول شروع کنید.', kb_panel());
        return;
    }
    if (!preg_match('/^[\p{L}\s\.\-\x{200C}]{3,60}$/u', $name)) {
        Tg::send($chat, '❌ نام نامعتبر است. فقط حروف (فارسی یا انگلیسی) بفرستید. مثال: علی رضایی');
        return;
    }
    Db::setSetting('cart_number', $digits);
    Db::kvSet('card_holder', $name);
    Db::setSetting('cart', 'on');
    admin_done($chat, "✅ اطلاعات کارت ذخیره و کارت‌به‌کارت فعال شد.\n\nکاربران این متن را می‌بینند:\n\n" . card_text());
    cd_menu($chat, 0);
}

/* ======================================================================
 *  Admin: crypto wallets (TRON / TON)
 * ==================================================================== */

function wl_menu(int $chat, int $mid, string $coin): void
{
    if (!isset(WALLETS[$coin])) {
        return;
    }
    $w    = WALLETS[$coin];
    $s    = Db::setting();
    $addr = trim((string)($s[$w['col']] ?? ''));
    $on   = ($s[$w['on']] ?? 'on') === 'on';
    $rate = rate_get($w['rate']);

    $t  = $w['icon'] . ' <b>آدرس ' . $w['title'] . "</b>\n\n";
    $t .= 'آدرس: ' . ($addr !== '' ? '<code>' . h($addr) . '</code>' : '❌ ثبت نشده') . "\n";
    $t .= 'وضعیت: ' . ($addr === '' ? '⚪️ نیاز به ثبت آدرس' : ($on ? '🟢 فعال' : '🔴 غیرفعال')) . "\n";
    $t .= 'نرخ تبدیل: ' . ($rate > 0 ? money($rate) . ' تومان (شارژ خودکار)' : '❌ تنظیم نشده (شارژ دستی توسط ادمین)') . "\n\n";
    $t .= "ℹ️ کاربر مقدار دلخواه را به این آدرس واریز می‌کند و لینک یا هش تراکنش را در ربات می‌فرستد. ربات تراکنش را روی بلاکچین بررسی می‌کند و موجودی را شارژ می‌کند.";

    $rows = [[cb('✏️ ' . ($addr !== '' ? 'تغییر' : 'ثبت') . ' آدرس', 'wl,' . $coin . ',set')]];
    if ($addr !== '') {
        $rows[] = [cb($on ? '🔴 غیرفعال کردن' : '🟢 فعال کردن', 'wl,' . $coin . ',tog'), cb('🗑 حذف آدرس', 'wl,' . $coin . ',del')];
    }
    $rows[] = [cb('💱 تنظیم نرخ', 'rt,menu')];
    $rows[] = btn_back_settings();
    screen($chat, $mid, $t, ik($rows));
}

function wl_action(int $chat, int $mid, string $coin, string $sub): ?array
{
    if (!isset(WALLETS[$coin])) {
        return alert('❌ نامعتبر');
    }
    $w = WALLETS[$coin];
    $s = Db::setting();
    switch ($sub) {
        case 'menu':
            wl_menu($chat, $mid, $coin);
            break;
        case 'set':
            prompt($chat, 'wl_set,' . $coin, '✏️ آدرس ' . $w['title'] . " را ارسال کنید.\n\n" . $w['hint']);
            break;
        case 'tog':
            if (trim((string)($s[$w['col']] ?? '')) === '') {
                return alert('ابتدا آدرس را ثبت کنید');
            }
            Db::setSetting($w['on'], ($s[$w['on']] ?? 'on') === 'on' ? 'off' : 'on');
            wl_menu($chat, $mid, $coin);
            break;
        case 'del':
            screen($chat, $mid, '⚠️ آدرس ' . $w['title'] . ' حذف شود؟', ik([[cb('✅ بله، حذف شود', 'wl,' . $coin . ',delok'), cb('❌ انصراف', 'wl,' . $coin . ',menu')]]));
            break;
        case 'delok':
            Db::setSetting($w['col'], '');
            wl_menu($chat, $mid, $coin);
            return alert('✅ آدرس حذف شد', false);
    }
    return null;
}

function step_wl_set(int $chat, string $coin, string $text): void
{
    if (!isset(WALLETS[$coin])) {
        set_step($chat, 'none');
        return;
    }
    $w    = WALLETS[$coin];
    $addr = trim($text);
    $ok   = $coin === 'tron' ? tron_valid($addr) : ton_valid($addr);
    if (!$ok) {
        Tg::send($chat, "❌ آدرس معتبر نیست.\n" . $w['hint']);
        return;
    }
    Db::setSetting($w['col'], $addr);
    Db::setSetting($w['on'], 'on');
    $rate = rate_get($w['rate']);
    admin_done(
        $chat,
        '✅ آدرس ' . $w['title'] . " ذخیره و فعال شد.\n\n<code>" . h($addr) . '</code>'
        . ($rate > 0 ? '' : "\n\n⚠️ نرخ " . COINS[$w['rate']]['short'] . ' هنوز تنظیم نشده؛ تا آن موقع شارژ دستی انجام می‌شود. از دکمهٔ «💱 نرخ ارز» تنظیم کنید.')
    );
    wl_menu($chat, 0, $coin);
}

/* ======================================================================
 *  Admin: exchange rates
 * ==================================================================== */

function rt_line(string $c): string
{
    $mode  = rate_mode($c);
    $rate  = rate_get($c);
    $label = ['manual' => '✍️ دستی', 'auto' => '🌐 خودکار (نوبیتکس)', 'api' => '🔗 API دلخواه'][$mode];
    $t     = COINS[$c]['icon'] . ' <b>' . COINS[$c]['name'] . "</b>\n";
    $t    .= '   نرخ فعلی: ' . ($rate > 0 ? '<b>' . money($rate) . '</b> تومان' : '❌ تنظیم نشده') . "\n";
    $t    .= '   حالت: ' . $label . "\n";
    if ($mode !== 'manual') {
        $t .= '   آخرین بروزرسانی: ' . ago((int)Db::kv("rate_{$c}_ts", '0')) . "\n";
        $e  = Db::kv("rate_{$c}_err", '');
        if ($e !== '') {
            $t .= '   ⚠️ ' . h($e) . "\n";
        }
    }
    return $t;
}

function rt_menu(int $chat, int $mid): void
{
    $t = "💱 <b>نرخ ارز (تومان)</b>\n\nاز این نرخ‌ها برای شارژ خودکار واریز ارز دیجیتال و قیمت‌گذاری خودکار استارز استفاده می‌شود.\n\n";
    foreach (array_keys(COINS) as $c) {
        $t .= rt_line($c) . "\n";
    }
    $t .= "✍️ دستی: خودتان نرخ را وارد می‌کنید.\n🌐 خودکار: نرخ لحظه‌ای از نوبیتکس.\n🔗 API دلخواه: آدرس API و مسیر قیمت را خودتان می‌دهید.\n\n⚠️ اگر نرخ تنظیم نباشد، شارژ خودکار انجام نمی‌شود و ادمین باید دستی شارژ کند.";
    screen($chat, $mid, $t, ik([
        [cb('✍️ نرخ دستی ترون', 'rt,man,trx'), cb('✍️ نرخ دستی گرام', 'rt,man,ton')],
        [cb('🌐 خودکار ترون', 'rt,auto,trx'), cb('🌐 خودکار گرام', 'rt,auto,ton')],
        [cb('🔗 API ترون', 'rt,api,trx'), cb('🔗 API گرام', 'rt,api,ton')],
        [cb('🔄 بروزرسانی نرخ‌ها', 'rt,upd')],
        btn_back_settings(),
    ]));
}

function rt_action(int $chat, int $mid, string $sub, string $arg, array $user): ?array
{
    $coin = $arg;
    switch ($sub) {
        case 'menu':
            rt_menu($chat, $mid);
            break;
        case 'man':
            if (!isset(COINS[$coin])) {
                return alert('❌ نامعتبر');
            }
            prompt($chat, 'rt_man,' . $coin, '✍️ نرخ هر ۱ ' . COINS[$coin]['name'] . " را به <b>تومان</b> ارسال کنید.\nمثال: <code>" . ($coin === 'ton' ? '150000' : '4200') . '</code>');
            break;
        case 'auto':
            if (!isset(COINS[$coin])) {
                return alert('❌ نامعتبر');
            }
            $err = null;
            $n   = rate_from_nobitex($coin, $err);
            if ($n === null) {
                return alert('❌ دریافت از نوبیتکس ناموفق بود (ممکن است سرور به نوبیتکس دسترسی نداشته باشد). از «API دلخواه» یا نرخ دستی استفاده کنید.');
            }
            Db::kvSet("rate_{$coin}_mode", 'auto');
            Db::kvSet("rate_{$coin}_val", (string)$n);
            Db::kvSet("rate_{$coin}_ts", (string)time());
            Db::kvSet("rate_{$coin}_err", '');
            rt_menu($chat, $mid);
            return alert('✅ نرخ خودکار فعال شد: ' . money($n) . ' تومان', false);
        case 'api':
            if (!isset(COINS[$coin])) {
                return alert('❌ نامعتبر');
            }
            prompt(
                $chat,
                'rt_api_url,' . $coin,
                '🔗 <b>API دلخواه ' . COINS[$coin]['name'] . "</b>\n\n<b>مرحله ۱ از ۳</b>\nآدرس API (فقط https) را ارسال کنید.\nAPI باید با GET یک JSON برگرداند که قیمت داخل آن باشد.\n\nمثال:\n<code>https://api.example.com/price?coin=trx</code>"
            );
            break;
        case 'upd':
            foreach (array_keys(COINS) as $c) {
                if (rate_mode($c) !== 'manual') {
                    rate_get($c, true);
                }
            }
            rt_menu($chat, $mid);
            return alert('🔄 نرخ‌ها بروزرسانی شد', false);
        case 'unit':
            [$coin, $unit] = array_pad(explode('-', $arg, 2), 2, '');
            $parts = explode(',', (string)$user['step'], 3);
            if (!isset(COINS[$coin]) || !in_array($unit, ['toman', 'rial'], true)
                || ($parts[0] ?? '') !== 'rt_api_unit' || ($parts[1] ?? '') !== $coin) {
                return alert('⚠️ این مرحله منقضی شده است. دوباره از منوی نرخ ارز شروع کنید.');
            }
            $d = json_decode(b64u_dec($parts[2] ?? ''), true);
            if (!is_array($d) || empty($d['u'])) {
                return alert('⚠️ اطلاعات مرحله از بین رفته است. دوباره شروع کنید.');
            }
            $err = null;
            $v   = rate_from_api((string)$d['u'], (string)($d['p'] ?? ''), $unit, $err);
            if ($v === null) {
                return alert('❌ ' . $err . ' — واحد دیگر را امتحان کنید یا از اول شروع کنید.');
            }
            Db::kvSet("rate_{$coin}_mode", 'api');
            Db::kvSet("rate_{$coin}_api_url", (string)$d['u']);
            Db::kvSet("rate_{$coin}_api_path", (string)($d['p'] ?? ''));
            Db::kvSet("rate_{$coin}_api_unit", $unit);
            Db::kvSet("rate_{$coin}_val", (string)$v);
            Db::kvSet("rate_{$coin}_ts", (string)time());
            Db::kvSet("rate_{$coin}_err", '');
            Db::kvSet("rate_{$coin}_try", (string)time());
            Tg::edit($chat, $mid, '✅ واحد انتخاب شد.');
            admin_done($chat, '✅ API ' . COINS[$coin]['name'] . ' تنظیم شد.' . "\nنرخ دریافت‌شده: <b>" . money($v) . '</b> تومان');
            rt_menu($chat, 0);
            break;
    }
    return null;
}

function step_rt_man(int $chat, string $coin, string $text): void
{
    $n = parse_int($text);
    if (!isset(COINS[$coin]) || $n === null || $n < 1 || $n > 1000000000) {
        Tg::send($chat, '❌ فقط یک عدد (تومان) ارسال کنید. مثال: 4200');
        return;
    }
    Db::kvSet("rate_{$coin}_mode", 'manual');
    Db::kvSet("rate_{$coin}_manual", (string)$n);
    admin_done($chat, '✅ نرخ ' . COINS[$coin]['name'] . ' روی <b>' . money($n) . '</b> تومان تنظیم شد (حالت دستی).');
    rt_menu($chat, 0);
}

function step_rt_api_url(int $chat, string $coin, string $text): void
{
    if (!isset(COINS[$coin]) || !safe_url($text)) {
        Tg::send($chat, '❌ آدرس نامعتبر است. فقط آدرس https معتبر بفرستید.');
        return;
    }
    prompt(
        $chat,
        'rt_api_path,' . $coin . ',' . b64u(json_encode(['u' => $text])),
        "🔗 <b>مرحله ۲ از ۳</b>\nمسیر عدد قیمت داخل JSON را ارسال کنید.\n\nمثال: اگر پاسخ <code>{\"data\":{\"price\":4200}}</code> است، بنویسید:\n<code>data.price</code>\n\nاگر مطمئن نیستید، علامت <code>-</code> بفرستید تا ربات خودش قیمت را تشخیص دهد."
    );
}

function step_rt_api_path(int $chat, string $arg, string $text): void
{
    [$coin, $b64] = array_pad(explode(',', $arg, 2), 2, '');
    $d = json_decode(b64u_dec($b64), true);
    if (!isset(COINS[$coin]) || !is_array($d) || empty($d['u'])) {
        set_step($chat, 'none');
        Tg::send($chat, '❌ مرحله منقضی شد. دوباره شروع کنید.', kb_panel());
        return;
    }
    if ($text !== '-' && !preg_match('/^[A-Za-z0-9_.\-]{1,100}$/', $text)) {
        Tg::send($chat, '❌ مسیر نامعتبر است. مثال: data.price یا علامت -');
        return;
    }
    $d['p'] = $text === '-' ? '' : $text;
    set_step($chat, 'rt_api_unit,' . $coin . ',' . b64u(json_encode($d)));
    Tg::send($chat, "🔗 <b>مرحله ۳ از ۳</b>\nقیمتی که API برمی‌گرداند به چه واحدی است؟", ik([
        [cb('تومان', 'rt,unit,' . $coin . '-toman'), cb('ریال', 'rt,unit,' . $coin . '-rial')],
    ]));
}

/* ======================================================================
 *  Admin: Fragment stars pricing
 * ==================================================================== */

function sp_products(): array
{
    return array_values(array_filter(
        Db::rows('SELECT * FROM ProductsF ORDER BY rowid'),
        fn($p) => in_array(p_type($p), ['stars', 'permium'], true)
    ));
}

function sp_menu(int $chat, int $mid): void
{
    $on    = sp_enabled();
    $rate  = rate_get('ton');
    $ts    = (int)Db::kv('sp_ts', '0');
    $err   = Db::kv('sp_err', '');
    $prods = sp_products();

    $t  = "⭐ <b>قیمت‌گذاری خودکار استارز و پرمیوم</b>\n\n";
    $t .= 'وضعیت: ' . ($on ? '🟢 روشن' : '🔴 خاموش') . "\n";
    $t .= "منبع قیمت: fragment.com/stars/buy و fragment.com/premium/gift\n";
    $t .= 'نرخ گرام (TON): ' . ($rate > 0 ? '<b>' . money($rate) . '</b> تومان' : '❌ تنظیم نشده (از «💱 نرخ ارز» تنظیم کنید)') . "\n";
    $t .= 'درصد سود: ' . rtrim(rtrim(sprintf('%.2F', sp_margin()), '0'), '.') . "٪\n";
    $t .= 'گرد کردن به بالا: ' . money(sp_round()) . " تومان\n";
    $t .= 'آخرین بروزرسانی: ' . ($ts > 0 ? ago($ts) . ' (' . Jalali::time($ts) . ')' : '—') . "\n";
    if ($err !== '') {
        $t .= '⚠️ ' . h($err) . "\n";
    }
    $t .= "\n<b>سرویس‌های استارز و پرمیوم:</b>\n";
    if (!$prods) {
        $t .= "هنوز سرویس استارز یا پرمیومی ساخته نشده است.\n";
    }
    foreach (array_slice($prods, 0, 25) as $p) {
        $t .= (p_is_auto($p) ? '🤖' : '✍️') . ' ' . h($p['name']) . ' — ' . p_qty($p) . ' — ' . money($p['price']) . ' ت' . (p_is_auto($p) ? ' — سود ' . pm_fmt(p_margin($p)) . '٪' : '') . "\n";
    }
    $t .= "\nℹ️ فرمول: قیمت فرگمنت (TON) × نرخ گرام × (۱ + سود).\n"
        . '• قیمت‌های Fragment هر ۳۰ دقیقه خودکار گرفته می‌شود.' . "\n"
        . '• هر بار که کاربر قیمت را می‌بیند، با نرخ لحظه‌ای گرام (دستی یا API) دوباره محاسبه می‌شود.' . "\n"
        . '• هنگام تغییر محسوس قیمت، به ادمین‌ها اطلاع داده می‌شود.';

    screen($chat, $mid, $t, ik([
        [cb($on ? '🔴 خاموش کردن بروزرسانی' : '🟢 روشن کردن بروزرسانی', 'sp,tog')],
        [cb('📈 سود پیش‌فرض', 'sp,margin'), cb('🔢 گرد کردن', 'sp,round')],
        [cb('📈 سود هر محصول', 'pm,menu')],
        [cb('🔄 بروزرسانی همین الان', 'sp,upd')],
        [cb('📋 انتخاب سرویس‌های خودکار', 'sp,list')],
        [cb('🤖 همه خودکار', 'sp,allauto'), cb('✍️ همه دستی', 'sp,allman')],
        btn_back_settings(),
    ]));
}

function sp_list(int $chat, int $mid): void
{
    $rows = [];
    foreach (array_slice(sp_products(), 0, 40) as $p) {
        $rows[] = [cb((p_is_auto($p) ? '🤖 ' : '✍️ ') . $p['name'] . ' — ' . money($p['number']) . (p_type($p) === 'stars' ? '⭐' : ' ماه') . ' — ' . money($p['price']), 'sp,tgp,' . $p['id'])];
    }
    if (!$rows) {
        screen($chat, $mid, 'هنوز سرویس استارز یا پرمیومی ساخته نشده است.', ik([[cb('◀️ بازگشت', 'sp,menu')]]));
        return;
    }
    $rows[] = [cb('◀️ بازگشت', 'sp,menu')];
    screen($chat, $mid, "📋 <b>انتخاب روش قیمت‌گذاری</b>\n\n🤖 = خودکار از Fragment\n✍️ = دستی\n\nروی هر سرویس بزنید تا تغییر کند.", ik($rows));
}

function sp_action(int $chat, int $mid, string $sub, string $arg): ?array
{
    switch ($sub) {
        case 'menu':
            sp_menu($chat, $mid);
            break;
        case 'tog':
            Db::kvSet('sp_on', sp_enabled() ? 'off' : 'on');
            sp_menu($chat, $mid);
            break;
        case 'margin':
            prompt($chat, 'sp_margin', '📈 درصد سود را ارسال کنید (مثلا <code>10</code> یا <code>7.5</code>).' . "\nمقدار فعلی: " . rtrim(rtrim(sprintf('%.2F', sp_margin()), '0'), '.') . '٪');
            break;
        case 'round':
            prompt($chat, 'sp_round', '🔢 قیمت‌ها به بالا به مضرب این عدد (تومان) گرد شوند. مثلا <code>1000</code>' . "\nمقدار فعلی: " . money(sp_round()));
            break;
        case 'upd':
            $r = sp_refresh(true);
            if (!$r['ok']) {
                return alert('❌ ' . $r['err']);
            }
            if ($r['changes']) {
                Tg::send($chat, sp_report($r['changes']));
            }
            sp_menu($chat, $mid);
            return alert($r['changes'] ? '✅ قیمت‌ها بروزرسانی شد' : '✅ قیمت‌ها بدون تغییر است', false);
        case 'list':
            sp_list($chat, $mid);
            break;
        case 'tgp':
            $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$arg]);
            if (!$p || !in_array(p_type($p), ['stars', 'permium'], true)) {
                return alert('سرویس یافت نشد');
            }
            if (p_is_auto($p)) {
                Db::exec("UPDATE ProductsF SET Fragment = 'none' WHERE id = ?", [(int)$arg]);
            } else {
                if (p_auto_key($p) === null) {
                    return alert(p_type($p) === 'stars' ? 'قیمت خودکار فقط برای ۵۰ استارز و بیشتر ممکن است' : 'قیمت خودکار فقط برای پرمیوم ۳، ۶ و ۱۲ ماهه ممکن است');
                }
                Db::exec("UPDATE ProductsF SET Fragment = 'auto' WHERE id = ?", [(int)$arg]);
                $r = sp_refresh(true, (int)$arg);
                if (!$r['ok']) {
                    Db::exec("UPDATE ProductsF SET Fragment = 'none' WHERE id = ?", [(int)$arg]);
                    sp_list($chat, $mid);
                    return alert('❌ ' . $r['err']);
                }
            }
            sp_list($chat, $mid);
            break;
        case 'allauto':
            Db::exec(
                "UPDATE ProductsF SET Fragment = 'auto' WHERE
                 (LOWER(TRIM(startsorpermium)) IN ('stars','starts','star') AND CAST(number AS INTEGER) >= 50)
                 OR (LOWER(TRIM(startsorpermium)) IN ('permium','premium') AND CAST(number AS INTEGER) IN (3,6,12))"
            );
            $r = sp_refresh(true);
            if ($r['changes']) {
                Tg::send($chat, sp_report($r['changes']));
            }
            sp_menu($chat, $mid);
            return $r['ok'] ? alert('✅ همه سرویس‌های استارز و پرمیوم خودکار شد', false) : alert('⚠️ ' . $r['err']);
        case 'allman':
            Db::exec("UPDATE ProductsF SET Fragment = 'none' WHERE LOWER(TRIM(startsorpermium)) IN ('stars','starts','star','permium','premium')");
            sp_menu($chat, $mid);
            return alert('✅ همه سرویس‌ها دستی شد', false);
    }
    return null;
}

function step_sp_value(int $chat, string $name, string $text): void
{
    if ($name === 'sp_margin') {
        $f = parse_float($text);
        if ($f === null || $f > 500) {
            Tg::send($chat, '❌ یک عدد بین 0 تا 500 ارسال کنید. مثال: 10');
            return;
        }
        Db::kvSet('sp_margin', rtrim(rtrim(sprintf('%.2F', $f), '0'), '.') ?: '0');
    } else {
        $n = parse_int($text);
        if ($n === null || $n < 1 || $n > 1000000) {
            Tg::send($chat, '❌ یک عدد بین 1 تا 1,000,000 ارسال کنید. مثال: 1000');
            return;
        }
        Db::kvSet('sp_round', (string)$n);
    }
    $r = sp_refresh(true);
    admin_done($chat, '✅ ذخیره شد.' . ($r['changes'] ? ' قیمت ' . count($r['changes']) . ' سرویس بروزرسانی شد.' : ''));
    sp_menu($chat, 0);
}

/* ======================================================================
 *  Admin: per-product profit (auto Fragment products only)
 * ==================================================================== */

function pm_products(): array
{
    return array_values(array_filter(sp_products(), 'p_is_auto'));
}

function pm_menu(int $chat, int $mid): void
{
    $prods = pm_products();
    $rate  = rate_get('ton');
    $t     = head('📈', 'تنظیم سود محصولات');
    if (!$prods) {
        $t .= "هنوز محصول <b>خودکار</b> (استارز یا پریمیوم با قیمت Fragment) نداری.\n\n"
            . 'محصولات دستی رو خودت قیمت‌گذاری می‌کنی و سودت رو مستقیم روی قیمت می‌زنی.';
        screen($chat, $mid, $t, ik([[cb('📈 سود پیش‌فرض', 'sp,margin')], [cb('◀️ بازگشت', 'sp,menu')]]));
        return;
    }
    $t .= "روی هر محصول بزن و درصد سودش رو بفرست؛ مثلا <code>20</code> یعنی ۲۰٪ سود روی قیمت Fragment.\n\n";
    $t .= '🔹 سود پیش‌فرض: <b>' . pm_fmt(sp_margin()) . "٪</b> (برای محصولاتی که سود جدا ندارن)\n";
    $t .= '🔹 نرخ گرام: ' . ($rate > 0 ? '<b>' . money($rate) . '</b> تومان' : '❌ تنظیم نشده') . "\n\n";
    $cache = fp_cache();
    $rows  = [];
    foreach (array_slice($prods, 0, 40) as $p) {
        $custom = pm_custom($p) !== null;
        $ton    = (float)($cache[(string)p_auto_key($p)]['ton'] ?? 0);
        $t     .= (p_type($p) === 'stars' ? '{e:stars}' : '{e:premium}') . ' ' . h(p_title($p)) . ' — سود <b>' . pm_fmt(p_margin($p)) . '٪</b>' . ($custom ? '' : ' (پیش‌فرض)')
            . ' — ' . money($p['price']) . ' ت' . ($ton > 0 ? ' — ' . rtrim(rtrim(sprintf('%.4F', $ton), '0'), '.') . ' TON' : '') . "\n";
        $rows[] = [cb((p_type($p) === 'stars' ? '{e:stars} ' : '{e:premium} ') . p_title($p) . ' — ' . pm_fmt(p_margin($p)) . '٪', 'pm,set,' . $p['id'])];
    }
    $t .= "\nℹ️ فرمول: قیمت Fragment (TON) × نرخ گرام × (۱ + سود). با تغییر سود، قیمت همون لحظه بروز می‌شه.";
    $rows[] = [cb('📈 سود پیش‌فرض', 'sp,margin')];
    $rows[] = [cb('◀️ بازگشت', 'sp,menu')];
    screen($chat, $mid, $t, ik($rows));
}

function pm_action(int $chat, int $mid, string $sub, string $arg): ?array
{
    if ($sub === 'menu') {
        pm_menu($chat, $mid);
        return null;
    }
    if ($sub === 'set') {
        $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$arg]);
        if (!$p || !p_is_auto($p)) {
            return alert('این محصول دیگه خودکار نیست');
        }
        $ton  = (float)(fp_cache()[(string)p_auto_key($p)]['ton'] ?? 0);
        $rate = rate_get('ton');
        prompt(
            $chat,
            'pm_val,' . (int)$p['id'],
            head('📈', 'سود ' . h(p_title($p)))
            . '📦 ' . h(p_qty($p)) . "\n"
            . ($ton > 0 ? '💎 قیمت Fragment: <b>' . rtrim(rtrim(sprintf('%.4F', $ton), '0'), '.') . "</b> TON\n" : '')
            . ($rate > 0 ? '🔹 نرخ گرام: ' . money($rate) . " تومان\n" : '')
            . '💰 قیمت فعلی: <b>' . money($p['price']) . "</b> تومان\n"
            . '📈 سود فعلی: <b>' . pm_fmt(p_margin($p)) . '٪</b>' . (pm_custom($p) === null ? ' (پیش‌فرض)' : '') . "\n\n"
            . "✍️ درصد سود جدید رو بفرست.\nمثال: <code>20</code> یعنی ۲۰٪ سود روی قیمت Fragment\n"
            . "<code>0</code> یعنی بدون سود\n<code>-</code> یعنی برگرد به سود پیش‌فرض (" . pm_fmt(sp_margin()) . '٪)'
        );
    }
    return null;
}

function step_pm_value(int $chat, string $pid, string $text): void
{
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$pid]);
    if (!$p || !p_is_auto($p)) {
        admin_done($chat, '⚠️ این محصول دیگه خودکار نیست.');
        return;
    }
    $text = trim($text);
    if ($text === '-') {
        Db::kvSet('pm_' . (int)$p['id'], '');
    } else {
        $f = parse_float($text);
        if ($f === null || $f < 0 || $f > 500) {
            Tg::send($chat, '❌ یه عدد بین 0 تا 500 بفرست. مثال: 20');
            return;
        }
        Db::kvSet('pm_' . (int)$p['id'], pm_fmt($f));
    }
    $r   = sp_refresh(true, (int)$p['id']);
    $new = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$p['id']]) ?: $p;
    admin_done(
        $chat,
        '✅ سود <b>' . h(p_title($new)) . '</b> روی <b>' . pm_fmt(p_margin($new)) . '٪</b>' . (pm_custom($new) === null ? ' (پیش‌فرض)' : '') . " تنظیم شد.\n"
        . '💰 قیمت جدید: <b>' . money($new['price']) . '</b> تومان'
        . ($r['ok'] ? '' : "\n⚠️ " . h($r['err']) . ' (قیمت بعد از دریافت نرخ بروز می‌شود)')
    );
    pm_menu($chat, 0);
}

function pr_choose(int $chat, int $pid, bool $auto): ?array
{
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if (!$p) {
        return alert('❌ سرویس یافت نشد');
    }
    if (!$auto) {
        Db::exec("UPDATE ProductsF SET Fragment = 'none' WHERE id = ?", [$pid]);
        prompt($chat, 'sub_price,' . $pid, 'مبلغ را به تومان وارد کنید');
        return null;
    }
    Db::exec("UPDATE ProductsF SET Fragment = 'auto' WHERE id = ?", [$pid]);
    $r = sp_refresh(true, $pid);
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if ($r['ok'] && $p && (int)$p['price'] > 0) {
        admin_done(
            $chat,
            "✅ سرویس با <b>قیمت خودکار</b> ایجاد شد!\n\n📦 " . h($p['name']) . ' — ' . p_qty($p) . ' — ' . money($p['price']) . " تومان\n🔄 از این پس قیمت به‌صورت لحظه‌ای از Fragment بروز می‌شود."
        );
        return null;
    }
    Db::exec("UPDATE ProductsF SET Fragment = 'none' WHERE id = ?", [$pid]);
    prompt($chat, 'sub_price,' . $pid, '⚠️ قیمت خودکار ممکن نشد: ' . h($r['err']) . "\n\nلطفا قیمت را دستی (به تومان) وارد کنید:");
    return null;
}

/* ======================================================================
 *  Boost orders (user side)
 * ==================================================================== */

function boost_target_ok(string $t): ?string
{
    $t = trim($t);
    if ($t === '' || mb_strlen($t) > 120) {
        return null;
    }
    if (preg_match('/^@[A-Za-z][A-Za-z0-9_]{3,31}$/', $t)) {
        return $t;
    }
    if (preg_match('~^(?:https?://)?(?:t|telegram)\.me/(?:\+[\w-]{8,}|joinchat/[\w-]{8,}|[A-Za-z][A-Za-z0-9_]{3,31}(?:/\d+)?)/?$~i', $t)) {
        return preg_match('~^https?://~i', $t) ? $t : 'https://' . $t;
    }
    return null;
}

function boost_product($pid): ?array
{
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$pid]);
    return ($p && p_type($p) === 'boost' && p_ready($p) && p_enabled($p)) ? $p : null;
}

function step_boost_target(array $m, string $arg): void
{
    $uid = (int)$m['chat']['id'];
    $p   = boost_product($arg);
    if (!$p) {
        set_step($uid, 'none');
        drop_reply_kb($uid);
        Tg::send($uid, '⛔ این محصول دیگه موجود نیست.', kb_main());
        return;
    }
    $t = boost_target_ok((string)($m['text'] ?? ''));
    if ($t === null) {
        Tg::send($uid, "⚠️ آدرس درست نیست.\nمثال: <code>@channel</code> یا <code>https://t.me/channel</code>");
        return;
    }
    prompt(
        $uid,
        'boost_count,' . (int)$p['id'] . '|' . b64u($t),
        head('{e:boost}', h(p_title($p))) . '🎯 مقصد: ' . h($t) . "\n\n"
        . "🔢 چندتا بوست می‌خوای؟ عدد رو بفرست\n"
        . '📌 حداقل سفارش: <b>' . boost_min() . '</b> بوست' . "\n"
        . '💰 قیمت هر بوست: <b>' . money($p['price']) . '</b> تومان'
    );
}

function step_boost_count(array $m, string $arg): void
{
    $uid = (int)$m['chat']['id'];
    [$pid, $b64] = array_pad(explode('|', $arg, 2), 2, '');
    $p      = boost_product($pid);
    $target = b64u_dec($b64);
    if (!$p || $target === '') {
        set_step($uid, 'none');
        drop_reply_kb($uid);
        Tg::send($uid, '⚠️ این مرحله منقضی شده یا محصول غیرفعاله. دوباره از اول شروع کن.', kb_main());
        return;
    }
    $n   = parse_int((string)($m['text'] ?? ''));
    $min = boost_min();
    if ($n === null || $n < $min || $n > BOOST_MAX) {
        Tg::send($uid, '⚠️ تعداد باید یه عدد بین ' . $min . ' تا ' . money(BOOST_MAX) . ' باشه.');
        return;
    }
    $price = (int)$p['price'];
    $total = $n * $price;
    $bal   = coin_of($uid);
    if ($bal < $total) {
        $max = intdiv($bal, max(1, $price));
        Tg::send(
            $uid,
            "⚠️ موجودیت کافی نیست.\n💰 مبلغ سفارش: " . money($total) . " تومان\n👛 موجودی تو: " . money($bal) . " تومان\n\n"
            . ($max >= $min ? "با موجودی فعلی حداکثر <b>$max</b> بوست می‌تونی بخری. یه تعداد دیگه بفرست یا حسابت رو شارژ کن." : 'اول حسابت رو شارژ کن 👇'),
            $max >= $min ? null : ik([[cb(BTN['topup'], 'add_coin')]])
        );
        return;
    }
    set_step($uid, 'boost_ok,' . (int)$p['id'] . '|' . $n . '|' . $b64);
    Tg::send(
        $uid,
        head('🧾', 'تایید نهایی سفارش بوست')
        . '📦 ' . h(p_title($p)) . "\n"
        . '🎯 مقصد: ' . h($target) . "\n"
        . "🔢 تعداد: <b>$n</b> بوست\n"
        . '💰 قیمت هر بوست: ' . money($price) . " تومان\n"
        . '💳 مبلغ کل: <b>' . money($total) . "</b> تومان\n\n"
        . 'همه‌چی درسته؟ اگه تایید کنی سفارش ثبت می‌شه 👇',
        ik([[cb('✅ تایید و ثبت سفارش', 'bo,ok'), cb('❌ انصراف', 'bo,no')]])
    );
}

function boost_confirm(int $chat, int $mid, int $uid, array $user, string $sub): ?array
{
    $parts = explode(',', (string)$user['step'], 2);
    if ($sub === 'no') {
        set_step($uid, 'none');
        drop_reply_kb($chat);
        screen($chat, $mid, '⛔ سفارش لغو شد. هر وقت خواستی برگرد!', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return null;
    }
    if (($parts[0] ?? '') !== 'boost_ok') {
        return alert('⚠️ این مرحله منقضی شده، دوباره از «خرید و سرویس‌ها» شروع کن.');
    }
    [$pid, $n, $b64] = array_pad(explode('|', (string)($parts[1] ?? ''), 3), 3, '');
    $p      = boost_product($pid);
    $target = b64u_dec($b64);
    $n      = (int)$n;
    if (!$p || $target === '' || $n < boost_min() || $n > BOOST_MAX) {
        set_step($uid, 'none');
        drop_reply_kb($chat);
        screen($chat, $mid, '⚠️ سفارش معتبر نیست یا محصول غیرفعاله.', ik([[cb('🏠 منوی اصلی', 'home')]]));
        return null;
    }
    $total   = $n * (int)$p['price'];
    $account = $target . ' | ' . $n . ' بوست';
    $oid     = order_create($uid, $p, $account, $total);
    set_step($uid, 'none');
    drop_reply_kb($chat);
    if ($oid === null) {
        screen($chat, $mid, '⚠️ موجودیت کافی نیست، اول حسابت رو شارژ کن 👇', ik([[cb(BTN['topup'], 'add_coin')], [cb('🏠 منوی اصلی', 'home')]]));
        return null;
    }
    screen(
        $chat,
        $mid,
        head('✅', 'سفارش بوستت ثبت شد!') . "🆔 شماره سفارش: <code>$oid</code>\n📦 " . h(p_title($p)) . "\n🎯 مقصد: " . h($target)
        . "\n🔢 تعداد: $n بوست\n💳 مبلغ: " . money($total) . " تومان\n\n🛡 تیم " . TEAM . ' سفارشت رو بررسی می‌کنه و بعد از تایید، بوست‌ها ارسال می‌شن.',
        ik([[cb('🏠 منوی اصلی', 'home')]])
    );
    $t  = "🚀 <b>سفارش بوست ثبت شد</b>\n\n";
    $t .= "🆔 سفارش: <code>$oid</code>\n";
    $t .= "👤 خریدار: <a href=\"tg://user?id=$uid\">$uid</a>\n";
    $t .= '🔰 سرویس: ' . h(p_title($p)) . "\n";
    $t .= '🎯 کانال/گروه: ' . h($target) . "\n";
    $t .= "🔢 تعداد: <b>$n</b> بوست\n";
    $t .= '💰 مبلغ کل: ' . money($total) . ' تومان';
    notify_admins($t, ik([
        [cb('✔️ تایید کردن', 'Compile,' . $oid)],
        [cb('✖️ رد کردن', 'notCompile,' . $oid)],
    ]));
    return null;
}

/* ======================================================================
 *  KYC (user side)
 * ==================================================================== */

function kyc_on(): bool
{
    return Db::kv('kyc_on', 'on') === 'on';
}

function kyc_row(int $uid): ?array
{
    return Db::row('SELECT * FROM kyc WHERE uid = ?', [$uid]);
}

function kyc_status(int $uid): string
{
    $r = kyc_row($uid);
    return $r ? (string)$r['status'] : 'none';
}

function kyc_need(int $uid): bool
{
    return kyc_on() && kyc_status($uid) !== 'approved';
}

function kyc_notice(int $chat, int $mid, int $uid): void
{
    $k  = kyc_row($uid);
    $st = $k ? (string)$k['status'] : 'none';
    if ($st === 'pending') {
        $t    = "⏳ مدارک احراز هویت شما ارسال شده و در حال بررسی توسط مدیریت است.\n\nبعد از بررسی نتیجه به شما اطلاع داده می‌شود و پس از تایید می‌توانید واریزی بزنید.";
        $rows = [[cb('🏠 منوی اصلی', 'home')]];
    } elseif ($st === 'rejected') {
        $t    = "❌ درخواست احراز هویت قبلی شما تایید نشد.\n\n📝 دلیل: " . h((string)$k['reason']) . "\n\nبرای واریزی باید دوباره احراز هویت انجام دهید.";
        $rows = [[cb('🪪 احراز هویت مجدد', 'kyc,start')], [cb('🏠 منوی اصلی', 'home')]];
    } else {
        $t = "⚠️ <b>کاربر گرامی، شما احراز هویت نکرده‌اید.</b>\n\n"
            . "به دلیل مسائل امنیتی، قبل از انجام واریزی باید احراز هویت انجام شود.\n"
            . "این کار فقط یک‌بار انجام می‌شود و پس از تایید مدیریت، همیشه می‌توانید به راحتی واریزی بزنید و دیگر نیازی به احراز هویت نیست.\n\n"
            . '👇 برای شروع روی دکمه «احراز هویت» بزنید.';
        $rows = [[cb('🪪 احراز هویت', 'kyc,start')], [cb('🏠 منوی اصلی', 'home')]];
    }
    screen($chat, $mid, $t, ik($rows));
}

function kyc_start(int $chat, int $uid): ?array
{
    if (!kyc_on()) {
        return alert('احراز هویت فعلا لازم نیست');
    }
    $st = kyc_status($uid);
    if ($st === 'approved') {
        return alert('✅ شما قبلاً احراز هویت شده‌اید');
    }
    if ($st === 'pending') {
        return alert('⏳ مدارک شما در حال بررسی است');
    }
    prompt(
        $chat,
        'kyc_card',
        "💳 لطفا شماره کارت 16 رقمی خود را وارد نمایید:\n"
        . '✅ شماره کارت شما باید برابر کارت بانکی باشد که در ویدیو احراز هویت ارسال می کنید'
    );
    return null;
}

function step_kyc_card(array $m): void
{
    $uid  = (int)$m['chat']['id'];
    $card = preg_replace('/[\s\-]+/', '', digits_en((string)($m['text'] ?? '')));
    if (!preg_match('/^\d{16}$/', (string)$card)) {
        Tg::send($uid, '❌ شماره کارت باید دقیقا ۱۶ رقم باشد. دوباره ارسال کنید.');
        return;
    }
    if (!luhn_ok($card)) {
        Tg::send($uid, '❌ این شماره کارت معتبر نیست. دوباره بررسی و ارسال کنید.');
        return;
    }
    $bank = card_bank($card);
    prompt(
        $uid,
        'kyc_video,' . $card,
        "👤 جهت ارسال مدارک:\n"
        . 'کارت بانکی + کارت ملی [ در صورت نداشتن شناسنامه ] + روی کاغذ با خودکار بنویسید [ این احراز هویت برای @' . h(bot_username() ?: 'bot') . " است ] + امضا + شماره تلفن به اسم دارنده کارت وجود داشته باشد .\n"
        . "پنج  مورد خواسته شده را کنار هم قرار دهید طوریکه هر پنج مورد واضح و قابل خواندن باشند سپس فیلم کوتاهی در حد چند ثانیه گرفته و ارسال کنید.\n\n"
        . "💯 موارد قابل توجه :\n"
        . "👈 موارد خواسته شده باید واضح باشند.\n"
        . "👈 فیلم ارسالی نباید زیاد طولانی باشد در حد چند ثانیه کافی است.\n"
        . "👈 در فیلم باید کارت بانکی + مدرک شناسایی + متن + امضا + شماره تلفن به اسم دارنده کارت وجود داشته باشد .\n"
        . "👈 مدرک شناسایی باید متعلق به دارنده کارت بانکی باشد.\n"
        . '✳️ شماره کارت شما: <code>' . $card . '</code>' . ($bank !== '' ? " ($bank)" : '') . "\n"
        . '🎥 لطفا فیلم آماده شده از احراز هویت مدارک خود را ارسال نمایید :'
    );
}

function step_kyc_video(array $m, string $card): void
{
    $uid = (int)$m['chat']['id'];
    $fid = '';
    $ft  = '';
    if (!empty($m['video']['file_id'])) {
        $fid = (string)$m['video']['file_id'];
        $ft  = 'video';
    } elseif (!empty($m['video_note']['file_id'])) {
        $fid = (string)$m['video_note']['file_id'];
        $ft  = 'video_note';
    } elseif (!empty($m['document']['file_id']) && str_starts_with((string)($m['document']['mime_type'] ?? ''), 'video/')) {
        $fid = (string)$m['document']['file_id'];
        $ft  = 'document';
    } elseif (!empty($m['animation']['file_id'])) {
        $fid = (string)$m['animation']['file_id'];
        $ft  = 'document';
    }
    if ($fid === '' || !preg_match('/^\d{16}$/', $card)) {
        Tg::send($uid, '❌ لطفا فقط <b>فیلم</b> احراز هویت را ارسال کنید (عکس یا متن قبول نیست).');
        return;
    }
    $from = $m['from'] ?? [];
    $name = trim((string)($from['first_name'] ?? '') . ' ' . (string)($from['last_name'] ?? ''));
    Db::exec(
        'INSERT INTO kyc (uid, status, card, reason, file_id, ftype, name, username, ts, upd)
         VALUES (?,?,?,?,?,?,?,?,?,?)
         ON CONFLICT(uid) DO UPDATE SET status = excluded.status, card = excluded.card, reason = excluded.reason,
            file_id = excluded.file_id, ftype = excluded.ftype, name = excluded.name, username = excluded.username,
            ts = excluded.ts, upd = excluded.upd',
        [$uid, 'pending', $card, '', $fid, $ft, $name, (string)($from['username'] ?? ''), time(), time()]
    );
    set_step($uid, 'none');
    drop_reply_kb($uid);
    Tg::send(
        $uid,
        "✅ <b>مدارک احراز هویت شما با موفقیت ارسال شد.</b>\n\nمدیریت در اولین فرصت آن را بررسی می‌کند و نتیجه همین‌جا به شما اطلاع داده می‌شود. ⏳",
        ik([[cb('🏠 منوی اصلی', 'home')]])
    );
    $k = kyc_row($uid);
    if ($k) {
        foreach (all_admins() as $a) {
            kyc_send_review($a, $k);
        }
    }
}

function kyc_caption(array $k): string
{
    $uid  = (int)$k['uid'];
    $name = trim((string)$k['name']);
    $un   = trim((string)$k['username']);
    $card = (string)$k['card'];
    $bank = card_bank($card);
    return "🪪 <b>درخواست احراز هویت</b>\n\n"
        . '👤 کاربر: <a href="tg://user?id=' . $uid . '">' . h($name !== '' ? $name : (string)$uid) . "</a>\n"
        . '🆔 آیدی: <code>' . $uid . "</code>\n"
        . '📛 یوزرنیم: ' . ($un !== '' ? '@' . h($un) : '—') . "\n"
        . '💳 شماره کارت: <code>' . h($card) . '</code>' . ($bank !== '' ? ' (' . h($bank) . ')' : '') . "\n"
        . '📅 ارسال: ' . Jalali::date((int)$k['ts']) . ' ' . Jalali::time((int)$k['ts']);
}

function kyc_send_review(int $to, array $k): void
{
    $cap = kyc_caption($k);
    $kb  = ik([[cb('✔️ تایید', 'kya,ok,' . (int)$k['uid']), cb('✖️ رد کردن', 'kya,no,' . (int)$k['uid'])]]);
    $fid = (string)$k['file_id'];
    $ok  = false;
    if ($k['ftype'] === 'video_note') {
        $r  = Tg::call('sendVideoNote', ['chat_id' => $to, 'video_note' => $fid]);
        $ok = $r && !empty($r['ok']);
        Tg::send($to, $cap, $kb);
        return;
    }
    $method = $k['ftype'] === 'document' ? 'sendDocument' : 'sendVideo';
    $field  = $k['ftype'] === 'document' ? 'document' : 'video';
    $r      = Tg::call($method, ['chat_id' => $to, $field => $fid, 'caption' => $cap, 'parse_mode' => 'HTML', 'reply_markup' => $kb]);
    $ok     = $r && !empty($r['ok']);
    if (!$ok) {
        Tg::send($to, $cap . "\n\n⚠️ ارسال فایل فیلم ممکن نشد.", $kb);
    }
}

/* ======================================================================
 *  KYC (admin side)
 * ==================================================================== */

function kya_counts(): array
{
    $o = ['pending' => 0, 'approved' => 0, 'rejected' => 0];
    foreach (Db::rows('SELECT status, COUNT(*) AS c FROM kyc GROUP BY status') as $r) {
        $o[(string)$r['status']] = (int)$r['c'];
    }
    return $o;
}

function kya_menu(int $chat, int $mid): void
{
    $c  = kya_counts();
    $on = kyc_on();
    $t  = "🪪 <b>احراز هویت کاربران</b>\n\n";
    $t .= 'وضعیت: ' . ($on ? '🟢 اجباری (قبل از واریزی ریالی)' : '🔴 غیرفعال') . "\n";
    $t .= '⏳ در انتظار بررسی: <b>' . $c['pending'] . "</b>\n";
    $t .= '✅ تایید شده: <b>' . $c['approved'] . "</b>\n";
    $t .= '❌ رد شده: <b>' . $c['rejected'] . "</b>\n\n";
    $t .= "ℹ️ وقتی احراز هویت روشن باشد، کاربر قبل از پرداخت با درگاه ریالی یا کارت‌به‌کارت باید شماره کارت و فیلم مدارک را بفرستد. فیلم برای همه ادمین‌ها ارسال می‌شود و با «تایید» یا «رد کردن» (همراه با دلیل) نتیجه به کاربر اطلاع داده می‌شود.";
    screen($chat, $mid, $t, ik([
        [cb($on ? '🔴 غیرفعال کردن احراز هویت' : '🟢 فعال کردن احراز هویت', 'kya,tog')],
        [cb('📋 درخواست‌های در انتظار (' . $c['pending'] . ')', 'kya,list')],
        [cb('🗑 لغو احراز یک کاربر', 'kya,rev')],
        btn_back_settings(),
    ]));
}

function kya_action(int $chat, int $mid, int $adminId, string $sub, string $arg): ?array
{
    switch ($sub) {
        case 'menu':
            kya_menu($chat, $mid);
            break;
        case 'tog':
            Db::kvSet('kyc_on', kyc_on() ? 'off' : 'on');
            kya_menu($chat, $mid);
            break;
        case 'list':
            $rows = [];
            foreach (Db::rows("SELECT * FROM kyc WHERE status = 'pending' ORDER BY ts LIMIT 40") as $k) {
                $label = trim((string)$k['name']) !== '' ? $k['name'] : (string)$k['uid'];
                $rows[] = [cb('👤 ' . $label . ' — ' . $k['uid'], 'kya,view,' . $k['uid'])];
            }
            if (!$rows) {
                screen($chat, $mid, '✅ درخواستی در انتظار بررسی نیست.', ik([[cb('◀️ بازگشت', 'kya,menu')]]));
                break;
            }
            $rows[] = [cb('◀️ بازگشت', 'kya,menu')];
            screen($chat, $mid, "📋 <b>درخواست‌های در انتظار</b>\nروی هر مورد بزنید تا فیلم دوباره ارسال شود.", ik($rows));
            break;
        case 'view':
            $k = kyc_row((int)$arg);
            if (!$k || $k['status'] !== 'pending') {
                return alert('این درخواست دیگر در انتظار نیست');
            }
            kyc_send_review($chat, $k);
            break;
        case 'rev':
            prompt($chat, 'kya_revoke', '🗑 آیدی عددی کاربری که می‌خواهید احراز هویت او لغو شود را ارسال کنید.');
            break;
        case 'ok':
        case 'no':
            $uid = (int)$arg;
            $k   = kyc_row($uid);
            if (!$k) {
                return alert('درخواست یافت نشد');
            }
            if ($k['status'] !== 'pending') {
                return alert('⚠️ این درخواست قبلاً بررسی شده است: ' . ($k['status'] === 'approved' ? 'تایید شده' : 'رد شده'));
            }
            if ($sub === 'no') {
                prompt($chat, 'kya_reason,' . $uid . '|' . $mid, '📝 دلیل رد کردن احراز هویت کاربر <code>' . $uid . '</code> را ارسال کنید.' . "\nاین دلیل برای کاربر نمایش داده می‌شود.");
                break;
            }
            $n = Db::exec("UPDATE kyc SET status = 'approved', reason = '', upd = ? WHERE uid = ? AND status = 'pending'", [time(), $uid]);
            if ($n === 0) {
                return alert('⚠️ این درخواست قبلاً بررسی شده است');
            }
            Tg::send(
                $uid,
                "✅ <b>احراز هویت شما با موفقیت تایید شد!</b> 🎉\n\nاز این پس نیازی به احراز هویت مجدد نیست و همیشه می‌توانید به راحتی موجودی حساب خود را افزایش دهید.",
                ik([[cb(BTN['topup'], 'add_coin')], [cb('🏠 منوی اصلی', 'home')]])
            );
            kya_mark($chat, $mid, '✅ تایید شد (ادمین ' . $adminId . ')');
            return alert('✅ احراز هویت تایید شد و به کاربر اطلاع داده شد', false);
    }
    return null;
}

function kya_mark(int $chat, int $mid, string $label): void
{
    if ($mid > 0) {
        Tg::call('editMessageReplyMarkup', [
            'chat_id'      => $chat,
            'message_id'   => $mid,
            'reply_markup' => ik([[cb($label, 'noop')]]),
        ]);
    }
}

function step_kya_reason(int $chat, string $arg, string $text): void
{
    [$uid, $mid] = array_pad(explode('|', $arg, 2), 2, '0');
    $uid = (int)$uid;
    if ($text === '' || mb_strlen($text) > 500) {
        Tg::send($chat, '❌ دلیل را به صورت متن (حداکثر ۵۰۰ کاراکتر) ارسال کنید.');
        return;
    }
    $n = Db::exec("UPDATE kyc SET status = 'rejected', reason = ?, upd = ? WHERE uid = ? AND status = 'pending'", [$text, time(), $uid]);
    if ($n === 0) {
        admin_done($chat, '⚠️ این درخواست قبلاً بررسی شده است.');
        return;
    }
    Tg::send(
        $uid,
        "❌ <b>متاسفانه احراز هویت شما تایید نشد</b>\n\n"
        . "📝 <b>دلیل رد شدن:</b>\n" . h($text) . "\n\n"
        . "🔄 لطفا ایراد بالا را برطرف کنید و دوباره احراز هویت را انجام دهید. دقت کنید همه مدارک کاملا واضح و خوانا باشند.\n"
        . '💬 در صورت وجود هرگونه سوال با پشتیبانی در ارتباط باشید.',
        ik([[cb('🪪 احراز هویت مجدد', 'kyc,start')], [cb('🏠 منوی اصلی', 'home')]])
    );
    kya_mark($chat, (int)$mid, '❌ رد شد');
    admin_done($chat, '✅ احراز هویت کاربر <code>' . $uid . '</code> رد شد و دلیل برای او ارسال شد.');
}

function step_kya_revoke(int $chat, string $text): void
{
    $id = parse_int($text);
    if ($id === null || kyc_row($id) === null) {
        Tg::send($chat, '❌ کاربری با این آیدی در لیست احراز هویت نیست.');
        return;
    }
    Db::exec('DELETE FROM kyc WHERE uid = ?', [$id]);
    admin_done($chat, '✅ احراز هویت کاربر <code>' . $id . '</code> لغو شد؛ برای واریز بعدی باید دوباره احراز هویت کند.');
}

/* ======================================================================
 *  Premium emoji channel (promo text after delivery)
 * ==================================================================== */

function em_default_text(): string
{
    return "✨ <b>میخوای ایموجی‌های خوشگل داشته باشی؟</b>\n\nبیا به کانال {channel} — اونجا کلی ایموجی پریمیومِ خفن برات گذاشتم! 😍";
}

function em_channel(): array
{
    $v = trim(Db::kv('em_chan', ''));
    if ($v === '') {
        return ['text' => '', 'url' => ''];
    }
    if ($v[0] === '@') {
        return ['text' => $v, 'url' => 'https://t.me/' . substr($v, 1)];
    }
    return ['text' => $v, 'url' => $v];
}

function em_promo(): array
{
    $ch = em_channel();
    if (Db::kv('em_on', 'on') !== 'on' || $ch['text'] === '') {
        return ['text' => '', 'markup' => null];
    }
    $tpl  = Db::kv('em_text', '') !== '' ? Db::kv('em_text') : em_default_text();
    $text = str_contains($tpl, '{channel}') ? str_replace('{channel}', $ch['text'], $tpl) : $tpl . "\n" . $ch['text'];
    return ['text' => $text, 'markup' => ik([[ub('✨ ورود به کانال ایموجی', $ch['url'])]])];
}

function em_menu(int $chat, int $mid): void
{
    $ch = em_channel();
    $on = Db::kv('em_on', 'on') === 'on';
    $t  = "✨ <b>کانال ایموجی پریمیوم</b>\n\n";
    $t .= 'وضعیت: ' . ($on ? '🟢 فعال' : '🔴 غیرفعال') . "\n";
    $t .= 'کانال: ' . ($ch['text'] !== '' ? h($ch['text']) : '❌ تنظیم نشده') . "\n";
    $t .= 'متن: ' . (Db::kv('em_text', '') !== '' ? '✏️ سفارشی' : '📄 پیش‌فرض') . "\n\n";
    $t .= "وقتی خرید کاربر تایید می‌شود، این متن و دکمهٔ ورود به کانال خودکار داخل پیام تحویل برای او ارسال می‌شود.\n\n";
    $t .= "<b>پیش‌نمایش متن:</b>\n" . (em_promo()['text'] ?: str_replace('{channel}', '@channel', em_default_text()));
    screen($chat, $mid, $t, ik([
        [cb('📝 تنظیم کانال', 'em,chan'), cb('✏️ ویرایش متن', 'em,text')],
        [cb($on ? '🔴 غیرفعال کردن' : '🟢 فعال کردن', 'em,tog'), cb('🔄 متن پیش‌فرض', 'em,reset')],
        [cb('🗑 حذف کانال', 'em,del')],
        btn_back_settings(),
    ]));
}

function em_action(int $chat, int $mid, string $sub): ?array
{
    switch ($sub) {
        case 'menu':
            em_menu($chat, $mid);
            break;
        case 'chan':
            prompt($chat, 'em_chan', "📝 یوزرنیم یا لینک کانال ایموجی پریمیوم را ارسال کنید.\nمثال: <code>@RhinoPremium</code> یا <code>https://t.me/RhinoPremium</code>");
            break;
        case 'text':
            prompt(
                $chat,
                'em_text',
                "✏️ متن دلخواه را ارسال کنید (HTML پشتیبانی می‌شود).\nبرای جایگذاری خودکار کانال از <code>{channel}</code> استفاده کنید.\n\nمثال:\n<code>میخوای ایموجی‌های خوشگل داشته باشی؟ بیا به چنل {channel} اونجا کلی ایموجی پریمیوم خفن برات گذاشتم 😍</code>"
            );
            break;
        case 'tog':
            Db::kvSet('em_on', Db::kv('em_on', 'on') === 'on' ? 'off' : 'on');
            em_menu($chat, $mid);
            break;
        case 'reset':
            Db::kvSet('em_text', '');
            em_menu($chat, $mid);
            return alert('متن به حالت پیش‌فرض برگشت', false);
        case 'del':
            Db::kvSet('em_chan', '');
            em_menu($chat, $mid);
            return alert('کانال حذف شد', false);
    }
    return null;
}

function step_em_chan(int $chat, string $text): void
{
    $t = trim($text);
    if (preg_match('/^@?([A-Za-z][A-Za-z0-9_]{3,31})$/', $t, $mm)) {
        $v = '@' . $mm[1];
    } elseif (preg_match('~^(?:https?://)?(?:t|telegram)\.me/(?:\+[\w-]{8,}|joinchat/[\w-]{8,}|[A-Za-z][A-Za-z0-9_]{3,31})/?$~i', $t)) {
        $v = preg_match('~^https?://~i', $t) ? $t : 'https://' . $t;
    } else {
        Tg::send($chat, '❌ آدرس نامعتبر است. مثال: @RhinoPremium یا https://t.me/RhinoPremium');
        return;
    }
    Db::kvSet('em_chan', $v);
    Db::kvSet('em_on', 'on');
    admin_done($chat, '✅ کانال ایموجی پریمیوم ثبت شد: ' . h($v));
    em_menu($chat, 0);
}

function step_em_text(int $chat, string $text): void
{
    if ($text === '' || mb_strlen($text) > 1000) {
        Tg::send($chat, '❌ متن را ارسال کنید (حداکثر ۱۰۰۰ کاراکتر).');
        return;
    }
    Db::kvSet('em_text', $text);
    admin_done($chat, '✅ متن ذخیره شد.');
    em_menu($chat, 0);
}

/* ======================================================================
 *  Admin: gift prices / boost prices / quick product creation
 * ==================================================================== */

function unit_products_count(string $type, int $number): int
{
    return (int)Db::val(
        'SELECT COUNT(*) FROM ProductsF WHERE LOWER(TRIM(startsorpermium)) = ? AND CAST(number AS INTEGER) = ?',
        [$type, $number]
    );
}

function quick_make(string $type, string $catName): int
{
    $made = 0;
    $time = Jalali::time();
    $date = Jalali::date();
    $defs = [];
    if ($type === 'gift') {
        foreach (GIFTS as $id => $g) {
            $defs[] = [$g['icon'] . ' ' . $g['name'], $id, (int)Db::kv('gift_price_' . $id, '0')];
        }
    } else {
        foreach (BOOSTS as $k => $b) {
            $defs[] = [$b['name'], $b['number'], (int)Db::kv('boost_price_' . $k, '0')];
        }
    }
    foreach ($defs as [$name, $num, $price]) {
        if ($price <= 0) {
            continue;
        }
        if (Db::val(
            'SELECT 1 FROM ProductsF WHERE LOWER(TRIM(startsorpermium)) = ? AND CAST(number AS INTEGER) = ? AND ProductsA = ?',
            [$type, $num, $catName]
        ) !== null) {
            continue;
        }
        do {
            $id = random_int(1000000, 9999999);
        } while (Db::val('SELECT 1 FROM ProductsF WHERE id = ?', [$id]) !== null);
        Db::exec(
            'INSERT INTO ProductsF (id, name, Description, time, date, price, ProductsA, Fragment, number, startsorpermium)
             VALUES (?,?,?,?,?,?,?,?,?,?)',
            [$id, $name, '', $time, $date, (string)$price, $catName, 'none', (string)$num, $type]
        );
        $made++;
    }
    return $made;
}

function gf_menu(int $chat, int $mid): void
{
    $t    = "🎁 <b>قیمت گیفت‌های استارزی</b>\n\nقیمت هر گیفت را (به تومان) دستی تنظیم کنید. با تغییر قیمت، همهٔ سرویس‌های آن گیفت هم خودکار بروز می‌شوند.\n\n";
    $rows = [];
    $btns = [];
    foreach (GIFTS as $id => $g) {
        $price = (int)Db::kv('gift_price_' . $id, '0');
        $cnt   = unit_products_count('gift', $id);
        $t    .= $g['icon'] . ' ' . $g['name'] . ' (' . $g['stars'] . '⭐) — ' . ($price > 0 ? '<b>' . money($price) . '</b> ت' : '❌ بدون قیمت') . ' — سرویس: ' . ($cnt > 0 ? "✅ $cnt" : '❌') . "\n";
        $btns[] = cb($g['icon'] . ' ' . $g['name'] . ($price > 0 ? ' — ' . money($price) : ''), 'gf,set,' . $id);
    }
    $rows = array_chunk($btns, 2);
    $rows[] = [cb('⚡ ساخت سریع سرویس‌ها', 'gf,mk')];
    $rows[] = btn_back_settings();
    $t .= "\nℹ️ «ساخت سریع سرویس‌ها» برای همهٔ گیفت‌هایی که قیمت دارند در یک سرویس اصلی، سرویس فرعی می‌سازد.";
    screen($chat, $mid, $t, ik($rows));
}

function gf_action(int $chat, int $mid, string $sub, string $arg): ?array
{
    switch ($sub) {
        case 'menu':
            gf_menu($chat, $mid);
            break;
        case 'set':
            $g = GIFTS[(int)$arg] ?? null;
            if (!$g) {
                return alert('گیفت نامعتبر');
            }
            prompt(
                $chat,
                'gf_price,' . (int)$arg,
                '💰 قیمت ' . $g['icon'] . ' <b>' . $g['name'] . '</b> را به تومان ارسال کنید.' . "\n(عدد 0 یعنی غیرفعال)\nقیمت فعلی: " . money((int)Db::kv('gift_price_' . (int)$arg, '0'))
            );
            break;
        case 'mk':
        case 'boost_mk':
            $cats = Db::rows('SELECT id, name FROM ProductsA ORDER BY rowid');
            if (!$cats) {
                return alert('❌ ابتدا یک سرویس اصلی بسازید');
            }
            $rows = [];
            foreach ($cats as $c) {
                $rows[] = [cb($c['name'], ($sub === 'mk' ? 'gf' : 'bp') . ',mkc,' . $c['id'])];
            }
            $rows[] = [cb('◀️ بازگشت', ($sub === 'mk' ? 'gf' : 'bp') . ',menu')];
            screen($chat, $mid, '⚡ سرویس‌ها در کدام سرویس اصلی ساخته شوند؟', ik($rows));
            break;
        case 'mkc':
            $cat = Db::row('SELECT name FROM ProductsA WHERE id = ?', [(int)$arg]);
            if (!$cat) {
                return alert('سرویس اصلی یافت نشد');
            }
            $n = quick_make('gift', (string)$cat['name']);
            gf_menu($chat, $mid);
            return alert($n > 0 ? "✅ $n سرویس ساخته شد" : 'سرویس جدیدی ساخته نشد (قیمت ندارند یا قبلاً ساخته شده‌اند)', false);
    }
    return null;
}

function step_gf_price(int $chat, string $arg, string $text): void
{
    $id = (int)$arg;
    $n  = parse_int($text);
    if (!isset(GIFTS[$id]) || $n === null || $n > 1000000000) {
        Tg::send($chat, '❌ فقط یک عدد (تومان) ارسال کنید. مثال: 45000');
        return;
    }
    Db::kvSet('gift_price_' . $id, (string)$n);
    Db::exec(
        "UPDATE ProductsF SET price = ? WHERE LOWER(TRIM(startsorpermium)) = 'gift' AND CAST(number AS INTEGER) = ?",
        [(string)$n, $id]
    );
    admin_done($chat, '✅ قیمت ' . GIFTS[$id]['icon'] . ' ' . GIFTS[$id]['name'] . ' روی <b>' . money($n) . '</b> تومان تنظیم شد.');
    gf_menu($chat, 0);
}

function bp_menu(int $chat, int $mid): void
{
    $t = "🚀 <b>قیمت بوست کانال و گروه</b>\n\nقیمت هر ۱ بوست را دستی (به تومان) تنظیم کنید.\n\n";
    foreach (BOOSTS as $k => $b) {
        $price = (int)Db::kv('boost_price_' . $k, '0');
        $cnt   = unit_products_count('boost', $b['number']);
        $t    .= '🚀 ' . $b['name'] . ' — ' . ($price > 0 ? '<b>' . money($price) . '</b> ت / هر بوست' : '❌ بدون قیمت') . ' — سرویس: ' . ($cnt > 0 ? "✅ $cnt" : '❌') . "\n";
    }
    $t .= "\n📌 حداقل سفارش: <b>" . boost_min() . '</b> بوست';
    screen($chat, $mid, $t, ik([
        [cb('💰 قیمت بوست ۱ الی ۵ روزه', 'bp,set,s')],
        [cb('💰 قیمت بوست ۳۰ روزه', 'bp,set,l')],
        [cb('📌 حداقل سفارش', 'bp,min')],
        [cb('⚡ ساخت سریع سرویس‌ها', 'bp,boost_mk')],
        btn_back_settings(),
    ]));
}

function bp_action(int $chat, int $mid, string $sub, string $arg): ?array
{
    switch ($sub) {
        case 'menu':
            bp_menu($chat, $mid);
            break;
        case 'set':
            if (!isset(BOOSTS[$arg])) {
                return alert('نامعتبر');
            }
            prompt(
                $chat,
                'bp_price,' . $arg,
                '💰 قیمت هر ۱ بوست برای <b>' . BOOSTS[$arg]['name'] . '</b> را به تومان ارسال کنید.' . "\n(عدد 0 یعنی غیرفعال)\nقیمت فعلی: " . money((int)Db::kv('boost_price_' . $arg, '0'))
            );
            break;
        case 'min':
            prompt($chat, 'bp_min', '📌 حداقل تعداد سفارش بوست را ارسال کنید.' . "\nمقدار فعلی: " . boost_min());
            break;
        case 'boost_mk':
            return gf_action($chat, $mid, 'boost_mk', '');
        case 'mkc':
            $cat = Db::row('SELECT name FROM ProductsA WHERE id = ?', [(int)$arg]);
            if (!$cat) {
                return alert('سرویس اصلی یافت نشد');
            }
            $n = quick_make('boost', (string)$cat['name']);
            bp_menu($chat, $mid);
            return alert($n > 0 ? "✅ $n سرویس ساخته شد" : 'سرویس جدیدی ساخته نشد (قیمت ندارند یا قبلاً ساخته شده‌اند)', false);
    }
    return null;
}

function step_bp_price(int $chat, string $arg, string $text): void
{
    $n = parse_int($text);
    if (!isset(BOOSTS[$arg]) || $n === null || $n > 1000000000) {
        Tg::send($chat, '❌ فقط یک عدد (تومان) ارسال کنید. مثال: 3500');
        return;
    }
    Db::kvSet('boost_price_' . $arg, (string)$n);
    Db::exec(
        "UPDATE ProductsF SET price = ? WHERE LOWER(TRIM(startsorpermium)) = 'boost' AND CAST(number AS INTEGER) = ?",
        [(string)$n, BOOSTS[$arg]['number']]
    );
    admin_done($chat, '✅ قیمت هر بوست برای ' . BOOSTS[$arg]['name'] . ' روی <b>' . money($n) . '</b> تومان تنظیم شد.');
    bp_menu($chat, 0);
}

function step_bp_min(int $chat, string $text): void
{
    $n = parse_int($text);
    if ($n === null || $n < 1 || $n > 10000) {
        Tg::send($chat, '❌ یک عدد بین 1 تا 10,000 ارسال کنید. مثال: 10');
        return;
    }
    Db::kvSet('boost_min', (string)$n);
    admin_done($chat, '✅ حداقل سفارش بوست روی <b>' . $n . '</b> تنظیم شد.');
    bp_menu($chat, 0);
}

function price_offer(int $chat, array $p): void
{
    $key   = unit_price_key($p);
    $cur   = $key !== null ? (int)Db::kv($key, '0') : 0;
    $boost = p_type($p) === 'boost';
    if ($cur > 0) {
        Tg::send(
            $chat,
            '💰 قیمت تنظیم‌شده برای «' . h(p_qty($p)) . '»: <b>' . money($cur) . '</b> تومان' . ($boost ? ' (هر بوست)' : '')
            . "\n\nاز همین قیمت استفاده شود یا قیمت جدید وارد می‌کنید؟",
            ik([
                [cb('✅ استفاده از قیمت فعلی', 'gpr,' . (int)$p['id'] . ',use')],
                [cb('✍️ قیمت جدید', 'gpr,' . (int)$p['id'] . ',new')],
            ])
        );
        return;
    }
    prompt($chat, 'sub_price,' . (int)$p['id'], $boost ? 'قیمت هر ۱ بوست را به تومان وارد کنید' : 'مبلغ را به تومان وارد کنید');
}

function price_pick(int $chat, int $pid, string $mode): ?array
{
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    if (!$p || !in_array(p_type($p), ['gift', 'boost'], true)) {
        return alert('❌ سرویس یافت نشد');
    }
    if ($mode === 'new') {
        prompt($chat, 'sub_price,' . $pid, p_type($p) === 'boost' ? 'قیمت هر ۱ بوست را به تومان وارد کنید' : 'مبلغ را به تومان وارد کنید');
        return null;
    }
    $cur = (int)Db::kv((string)unit_price_key($p), '0');
    if ($cur <= 0) {
        return alert('قیمتی تنظیم نشده است');
    }
    Db::exec('UPDATE ProductsF SET price = ? WHERE id = ?', [(string)$cur, $pid]);
    $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [$pid]);
    admin_done($chat, '✅ سرویس با موفقیت ایجاد شد!' . ($p ? "\n\n📦 " . h($p['name']) . ' — ' . p_qty($p) . ' — ' . money($p['price']) . ' تومان' : ''));
    return null;
}

/* ======================================================================
 *  Background tick (CLI: `php index.php tick`)
 * ==================================================================== */

function cron_tick(): void
{
    if (Config::$token === '') {
        return;
    }
    try {
        foreach (array_keys(COINS) as $c) {
            if (rate_mode($c) !== 'manual') {
                rate_get($c, true);
            }
        }
        Db::exec('DELETE FROM joincache WHERE ts < ?', [time() - 86400]);

        sp_refresh(false);
        $big = sp_notify_changes();
        if ($big) {
            notify_admins(sp_report($big));
        }
    } catch (Throwable $e) {
        logx('tick failed: ' . $e->getMessage());
    }
}

/* ======================================================================
 *  Admin: steps
 * ==================================================================== */

function split_id_amount(string $text): ?array
{
    $parts = preg_split('/[\s,،]+/u', trim(digits_en($text)));
    if (!$parts || count($parts) < 2 || !ctype_digit($parts[0])) {
        return null;
    }
    $amt = parse_int($parts[1]);
    return $amt === null ? null : [(int)$parts[0], $amt];
}

function step_admin(string $name, string $arg, array $m): bool
{
    $chat = (int)$m['chat']['id'];
    $text = trim((string)($m['text'] ?? ''));
    $date = Jalali::date();
    $time = Jalali::time();

    switch ($name) {
        case 'bc_send':
            broadcast($chat, $m, false);
            return true;
        case 'bc_fwd':
            broadcast($chat, $m, true);
            return true;

        case 'msg_user':
            if (!preg_match('/^\s*(\d+)\s*[,\n]\s*(.+)$/su', $text, $mm)) {
                Tg::send($chat, "❌ فرمت اشتباه است.\n<code>id,message</code>");
                return true;
            }
            Tg::send((int)$mm[1], "👨‍💻 یک پیام از طرف مدیریت براتون امد\n\n" . $mm[2]);
            admin_done($chat, '✅ انجام شد');
            return true;

        case 'reply_user':
            if ($text === '') {
                Tg::send($chat, '❌ فقط متن ارسال کنید');
                return true;
            }
            Tg::send((int)$arg, "👨‍💻 پاسخ پشتیبانی:\n\n" . $text);
            admin_done($chat, '✅ پیام برای کاربر ارسال شد');
            return true;

        case 'adm_add':
            step_adm_add($chat, $m);
            return true;
        case 'fj_add':
            step_fj_add($chat, $m);
            return true;
        case 'gw_key':
            step_gw_key($chat, $m);
            return true;
        case 'gw_min':
        case 'gw_max':
            step_gw_limit($chat, $name, $text);
            return true;
        case 'card_num':
            step_card_num($chat, $text);
            return true;
        case 'card_name':
            step_card_name($chat, $arg, $text);
            return true;
        case 'wl_set':
            step_wl_set($chat, $arg, $text);
            return true;
        case 'rt_man':
            step_rt_man($chat, $arg, $text);
            return true;
        case 'rt_api_url':
            step_rt_api_url($chat, $arg, $text);
            return true;
        case 'rt_api_path':
            step_rt_api_path($chat, $arg, $text);
            return true;
        case 'rt_api_unit':
            Tg::send($chat, '☝️ لطفا یکی از دکمه‌های «تومان» یا «ریال» را در پیام بالا انتخاب کنید.');
            return true;
        case 'sp_margin':
        case 'sp_round':
            step_sp_value($chat, $name, $text);
            return true;
        case 'pm_val':
            step_pm_value($chat, $arg, $text);
            return true;

        case 'coin_add':
        case 'coin_sub':
            $pair = split_id_amount($text);
            if (!$pair || !user_exists($pair[0])) {
                Tg::send($chat, "❌ فرمت اشتباه است یا کاربر وجود ندارد.\n<code>id,amount</code>");
                return true;
            }
            if ($name === 'coin_add') {
                coin_add($pair[0], $pair[1]);
                Tg::send($pair[0], '💰 مبلغ ' . money($pair[1]) . ' تومان به موجودی شما اضافه شد.');
                admin_done($chat, '✅ موجودی کاربر با موفقیت افزایش یافت');
            } else {
                if (!coin_sub($pair[0], $pair[1])) {
                    Db::exec('UPDATE users SET coin = ? WHERE id = ?', ['0', $pair[0]]);
                }
                admin_done($chat, '✅ موجودی کاربر با موفقیت کاهش یافت');
            }
            return true;

        case 'cc_amount':
            $amt = parse_int($text);
            $uid = (int)$arg;
            if ($amt === null || $amt <= 0 || !user_exists($uid)) {
                Tg::send($chat, '❌ مبلغ نامعتبر است');
                return true;
            }
            coin_add($uid, $amt);
            Tg::send($uid, '💰 مبلغ ' . money($amt) . ' تومان به موجودی شما اضافه شد.');
            admin_done($chat, "✅ مبلغ " . money($amt) . " تومان به کاربر <code>$uid</code> اضافه شد");
            return true;

        case 'check_user':
            $id = parse_int($text);
            if ($id === null) {
                Tg::send($chat, '❌ فقط ایدی عددی ارسال کنید');
                return true;
            }
            admin_check_user($chat, $id);
            return true;

        case 'ban_user':
        case 'unban_user':
            $id = parse_int($text);
            if ($id === null || !user_exists($id)) {
                Tg::send($chat, '❌ کاربر یافت نشد');
                return true;
            }
            Db::exec('UPDATE users SET account = ? WHERE id = ?', [$name === 'ban_user' ? 'ban' : 'none', $id]);
            admin_done($chat, $name === 'ban_user' ? '✅ کاربر با موفقیت بن شد' : '✅ کاربر با موفقیت از بن خارج شد');
            return true;

        case 'set_start':
        case 'set_help':
        case 'set_rules':
            if ($text === '') {
                Tg::send($chat, '❌ فقط متن ارسال کنید');
                return true;
            }
            $col = ['set_start' => 'start', 'set_help' => 'help', 'set_rules' => 'ruls'][$name];
            if ($text === '-' || $text === 'پیش‌فرض') {
                Db::kvSet('txt_custom_' . $col, '0');
                admin_done($chat, '✅ متن به حالت پیش‌فرض ' . BRAND . ' برگشت');
                return true;
            }
            Db::setText($col, $text);
            Db::kvSet('txt_custom_' . $col, '1');
            admin_done($chat, '✅ متن با موفقیت تنظیم شد');
            return true;

        case 'org_name':
            if ($text === '' || mb_strlen($text) > 60) {
                Tg::send($chat, '❌ نام نامعتبر است');
                return true;
            }
            if (Db::val('SELECT 1 FROM ProductsA WHERE name = ?', [$text]) !== null) {
                Tg::send($chat, '❌ سرویسی با این نام وجود دارد');
                return true;
            }
            do {
                $id = random_int(1000000, 9999999);
            } while (Db::val('SELECT 1 FROM ProductsA WHERE id = ?', [$id]) !== null);
            Db::exec('INSERT INTO ProductsA (id, name, Description, time, date) VALUES (?,?,?,?,?)', [$id, $text, '', $time, $date]);
            prompt($chat, 'org_desc,' . $id, "توضیحات سرویس را ارسال کنید\n(برای رد کردن «-» بفرستید)");
            return true;

        case 'org_desc':
            Db::exec('UPDATE ProductsA SET Description = ? WHERE id = ?', [$text === '-' ? '' : $text, (int)$arg]);
            admin_done($chat, '✅ سرویس با موفقیت اضافه شد');
            return true;

        case 'sub_name':
            if ($text === '' || mb_strlen($text) > 60) {
                Tg::send($chat, '❌ نام نامعتبر است');
                return true;
            }
            do {
                $id = random_int(1000000, 9999999);
            } while (Db::val('SELECT 1 FROM ProductsF WHERE id = ?', [$id]) !== null);
            Db::exec(
                'INSERT INTO ProductsF (id, name, Description, time, date, price, ProductsA, Fragment, number, startsorpermium)
                 VALUES (?,?,?,?,?,?,?,?,?,?)',
                [$id, $text, '', $time, $date, '0', 'none', 'none', '0', 'none']
            );
            $arg = (string)$id;
            // fallthrough: product text/banner is generated automatically, no description step
        case 'sub_desc':
            $pid = (int)$arg;
            if ($name === 'sub_desc') {
                Db::exec('UPDATE ProductsF SET Description = ? WHERE id = ?', [$text === '-' ? '' : $text, $pid]);
            }
            $cats = Db::rows('SELECT id, name FROM ProductsA ORDER BY rowid');
            if (!$cats) {
                Db::exec('DELETE FROM ProductsF WHERE id = ?', [$pid]);
                admin_done($chat, '❌ ابتدا یک سرویس اصلی بسازید.');
                return true;
            }
            $rows = [];
            foreach ($cats as $c) {
                $rows[] = [cb($c['name'], 'setcat,' . $pid . ',' . $c['id'])];
            }
            set_step($chat, 'none');
            Tg::send($chat, '✅ این سرویس زیرمجموعه کدام سرویس اصلی باشد؟', ik($rows));
            return true;

        case 'sub_num':
            $n = parse_int($text);
            if ($n === null || $n <= 0) {
                Tg::send($chat, '❌ فقط عدد ارسال کنید');
                return true;
            }
            Db::exec('UPDATE ProductsF SET number = ? WHERE id = ?', [(string)$n, (int)$arg]);
            p_autoname((int)$arg);
            $pp = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$arg]);
            if ($pp && p_auto_key($pp) !== null) {
                set_step($chat, 'none');
                Tg::send(
                    $chat,
                    "💰 <b>روش قیمت‌گذاری این سرویس را انتخاب کنید</b>\n\n🤖 <b>خودکار:</b> قیمت لحظه‌ای از " . (p_type($pp) === 'stars' ? 'fragment.com/stars/buy' : 'fragment.com/premium/gift') . " × نرخ گرام + درصد سود، و همیشه بروز می‌ماند.\n✍️ <b>دستی:</b> خودتان مبلغ را وارد می‌کنید.",
                    ik([
                        [cb('🤖 قیمت خودکار از Fragment', 'pr_auto,' . (int)$arg)],
                        [cb('✍️ قیمت دستی', 'pr_manual,' . (int)$arg)],
                    ])
                );
                return true;
            }
            prompt($chat, 'sub_price,' . $arg, 'مبلغ را به تومان وارد کنید');
            return true;

        case 'sub_price':
            $n = parse_int($text);
            if ($n === null || $n <= 0) {
                Tg::send($chat, '❌ فقط عدد ارسال کنید');
                return true;
            }
            Db::exec('UPDATE ProductsF SET price = ? WHERE id = ?', [(string)$n, (int)$arg]);
            $p = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$arg]);
            if ($p && unit_price_key($p) !== null) {
                unit_price_set($p, $n);
            }
            admin_done($chat, '✅ سرویس با موفقیت ایجاد شد!' . ($p ? "\n\n📦 " . h($p['name']) . ' — ' . p_qty($p) . ' — ' . money($n) . ' تومان' . (p_type($p) === 'boost' ? ' (هر بوست)' : '') : ''));
            return true;

        case 'gf_price':
            step_gf_price($chat, $arg, $text);
            return true;
        case 'bp_price':
            step_bp_price($chat, $arg, $text);
            return true;
        case 'bp_min':
            step_bp_min($chat, $text);
            return true;
        case 'em_chan':
            step_em_chan($chat, $text);
            return true;
        case 'em_text':
            step_em_text($chat, $text);
            return true;
        case 'kya_reason':
            step_kya_reason($chat, $arg, $text);
            return true;
        case 'kya_revoke':
            step_kya_revoke($chat, $text);
            return true;
    }
    return false;
}

const ADMIN_STEPS = [
    'bc_send', 'bc_fwd', 'msg_user', 'reply_user', 'coin_add', 'coin_sub', 'cc_amount',
    'check_user', 'ban_user', 'unban_user', 'set_start', 'set_help', 'set_rules',
    'org_name', 'org_desc', 'sub_name', 'sub_desc', 'sub_num', 'sub_price',
    'adm_add', 'fj_add', 'gw_key', 'gw_min', 'gw_max', 'card_num', 'card_name', 'wl_set',
    'rt_man', 'rt_api_url', 'rt_api_path', 'rt_api_unit', 'sp_margin', 'sp_round', 'pm_val',
    'gf_price', 'bp_price', 'bp_min', 'em_chan', 'em_text', 'kya_reason', 'kya_revoke',
];

/* ======================================================================
 *  Update handlers
 * ==================================================================== */

function handle_step(array $m, array $user, bool $admin): void
{
    $chat = (int)$m['chat']['id'];
    [$name, $arg] = array_pad(explode(',', (string)$user['step'], 2), 2, '');

    if (in_array($name, ADMIN_STEPS, true)) {
        if (!$admin) {
            set_step($chat, 'none');
            return;
        }
        if (step_admin($name, $arg, $m)) {
            return;
        }
    }

    $isText = isset($m['text']) && $m['text'] !== '';
    switch ($name) {
        case 'support':
            step_support($m);
            return;
        case 'idpay_amount':
            step_idpay_amount($m);
            return;
        case 'crypto_ton':
            $isText ? step_crypto_ton($m) : Tg::send($chat, '❌ لینک تراکنش را به صورت متن ارسال کنید');
            return;
        case 'crypto_tron':
            $isText ? step_crypto_tron($m) : Tg::send($chat, '❌ لینک تراکنش را به صورت متن ارسال کنید');
            return;
        case 'card_receipt':
            step_card_receipt($m);
            return;
        case 'buy_account':
            step_buy_account($m, $arg);
            return;
        case 'boost_target':
            $isText ? step_boost_target($m, $arg) : Tg::send($chat, '❌ یوزرنیم یا لینک را به صورت متن ارسال کنید');
            return;
        case 'boost_count':
            $isText ? step_boost_count($m, $arg) : Tg::send($chat, '❌ تعداد را به صورت عدد ارسال کنید');
            return;
        case 'boost_ok':
            Tg::send($chat, '☝️ لطفا یکی از دکمه‌های «تایید» یا «انصراف» را در پیام بالا انتخاب کنید.');
            return;
        case 'kyc_card':
            $isText ? step_kyc_card($m) : Tg::send($chat, '❌ شماره کارت را به صورت متن ارسال کنید');
            return;
        case 'kyc_video':
            step_kyc_video($m, $arg);
            return;
        case 'transfer_to':
            step_transfer_to($m);
            return;
        case 'transfer_amt':
            step_transfer_amt($m, $arg);
            return;
    }
    set_step($chat, 'none');
}

function on_message(array $m): void
{
    if (($m['chat']['type'] ?? '') !== 'private') {
        return;
    }
    $chat = (int)$m['chat']['id'];
    $uid  = (int)($m['from']['id'] ?? 0);
    if ($uid <= 0 || !empty($m['from']['is_bot'])) {
        return;
    }
    $text  = trim((string)($m['text'] ?? ''));
    $admin = is_admin($uid);
    $isNew = !user_exists($uid);
    $user  = user_get($uid);

    if (!gate($uid, $admin, $chat, $user)) {
        return;
    }
    $step = (string)$user['step'];
    $norm = $text === '' ? '' : Pe::label($text);

    if ($norm !== '' && $norm === Pe::label(BTN['back'])) {
        set_step($chat, 'none');
        drop_reply_kb($chat);
        menu_main($chat);
        return;
    }
    if (str_starts_with($text, '/start')) {
        set_step($chat, 'none');
        if ($step !== 'none') {
            drop_reply_kb($chat);
        }
        if ($isNew) {
            welcome_new($chat, (string)($m['from']['first_name'] ?? ''));
        } else {
            menu_main($chat);
        }
        return;
    }
    if ($admin) {
        if ($text === '/admin') {
            set_step($chat, 'none');
            Tg::send($chat, "📝 <b>پنل مدیریت " . BRAND . "</b>\n\nهر بخش رو از دکمه‌های پایین انتخاب کن 👇", kb_panel());
            return;
        }
        if ($norm !== '') {
            foreach (ADM as $lbl) {
                if (Pe::label($lbl) === $norm) {
                    set_step($chat, 'none');
                    admin_button($lbl, $chat);
                    return;
                }
            }
        }
    }
    if ($step !== 'none') {
        handle_step($m, $user, $admin);
        return;
    }
    menu_main($chat);
}

function on_callback(array $cq): void
{
    $cbid = (string)$cq['id'];
    $uid  = (int)($cq['from']['id'] ?? 0);
    $msg  = $cq['message'] ?? [];
    $chat = (int)($msg['chat']['id'] ?? $uid);
    $mid  = (int)($msg['message_id'] ?? 0);
    $data = (string)($cq['data'] ?? '');
    if ($uid <= 0 || $data === '' || ($msg['chat']['type'] ?? 'private') !== 'private') {
        Tg::answer($cbid);
        return;
    }
    $admin = is_admin($uid);
    $user  = user_get($uid);

    if (!gate($uid, $admin, $chat, $user, $cbid, $data === 'joined')) {
        return;
    }
    [$cmd, $a, $b] = array_pad(explode(',', $data, 3), 3, '');

    if (in_array($cmd, ADMIN_CALLBACKS, true) && !$admin) {
        Tg::answer($cbid, 'این بخش مخصوص ادمینه', true);
        return;
    }

    $ans = null;
    switch ($cmd) {
        case 'noop':
            break;
        case 'joined':
            if (missing_channels($uid, true)) {
                $ans = ['⚠️ هنوز توی همه‌ی کانال‌ها عضو نشدی، یه بار دیگه چک کن', true];
            } else {
                $ans = ['✅ عضویتت تایید شد، خوش اومدی!', false];
                menu_main($chat, $mid);
            }
            break;
        case 'home':
            if ((string)$user['step'] !== 'none') {
                set_step($chat, 'none');
                drop_reply_kb($chat);
            }
            menu_main($chat, $mid);
            break;
        case 'account':
            cb_account($chat, $uid, $mid);
            break;
        case 'help':
            cb_help($chat, $mid);
            break;
        case 'guide':
            cb_text($chat, 'help');
            break;
        case 'rules':
            cb_text($chat, 'ruls');
            break;
        case 'support':
            prompt($chat, 'support', head('👮🏻', 'پشتیبانی ' . BRAND) . "هر سوال، پیشنهاد یا مشکلی داری همین‌جا برامون بنویس ✍️\nتیم " . TEAM . ' در اسرع وقت جوابت رو می‌ده.');
            break;
        case 'my_bots':
            cb_services($chat, $mid);
            break;
        case 'hello':
            cb_category($chat, $mid, (int)$a);
            break;
        case 'buy':
            cb_product($chat, $uid, $mid, (int)$a);
            break;
        case 'ok':
            $ans = cb_buy_start($chat, $uid, (int)$a);
            break;
        case 'add_coin':
            cb_topup($chat, $mid);
            break;
        case 'pay_crypto':
            cb_pay_crypto($chat, $mid);
            break;
        case 'pay_idpay':
            $ans = cb_pay_method($chat, 'idpay');
            break;
        case 'pay_ton':
            $ans = cb_pay_method($chat, 'ton');
            break;
        case 'pay_tron':
            $ans = cb_pay_method($chat, 'tron');
            break;
        case 'pay_card':
            $ans = cb_pay_method($chat, 'card');
            break;
        case 'transfer':
            prompt($chat, 'transfer_to', head('💸', 'انتقال موجودی') . 'آیدی عددی کاربری که می‌خوای براش موجودی بفرستی رو بنویس ✍️');
            break;

        case 'Compile':
        case 'notCompile':
            $ans = admin_order($chat, $mid, $a, $cmd === 'Compile', $uid);
            break;
        case 'cc':
            prompt($chat, 'cc_amount,' . (int)$a, '💰 مبلغ شارژ را به تومان برای کاربر ' . (int)$a . ' ارسال کنید');
            break;
        case 'reply':
            prompt($chat, 'reply_user,' . (int)$a, '✍️ پاسخ خود را برای کاربر ' . (int)$a . ' ارسال کنید');
            break;

        case 'svc_add_org':
            prompt($chat, 'org_name', '📝 نام سرویس را ارسال کنید');
            break;
        case 'svc_add_sub':
            if ((int)Db::val('SELECT COUNT(*) FROM ProductsA') === 0) {
                $ans = ['❌ ابتدا یک سرویس اصلی بسازید', true];
            } else {
                prompt($chat, 'sub_name', "📝 نام سرویس را ارسال کنید\n\n💡 اگه «-» بفرستید، نام و بنر و توضیحات محصول (طبق نوع و مقدار) خودکار توسط ربات ساخته می‌شود.");
            }
            break;
        case 'svc_del_org':
            admin_service_lists($chat, $mid, 'org');
            break;
        case 'svc_del_sub':
            admin_service_lists($chat, $mid, 'sub');
            break;
        case 'delA':
            $cat = Db::row('SELECT name FROM ProductsA WHERE id = ?', [(int)$a]);
            if ($cat) {
                Db::tx(function () use ($cat, $a) {
                    Db::exec('DELETE FROM ProductsF WHERE ProductsA = ?', [(string)$cat['name']]);
                    Db::exec('DELETE FROM ProductsA WHERE id = ?', [(int)$a]);
                });
            }
            admin_service_lists($chat, $mid, 'org');
            $ans = ['✅ سرویس با موفقیت حذف شد', false];
            break;
        case 'delF':
            Db::exec('DELETE FROM ProductsF WHERE id = ?', [(int)$a]);
            admin_service_lists($chat, $mid, 'sub');
            $ans = ['✅ سرویس با موفقیت حذف شد', false];
            break;
        case 'setcat':
            $cat = Db::row('SELECT name FROM ProductsA WHERE id = ?', [(int)$b]);
            if ($cat && Db::exec('UPDATE ProductsF SET ProductsA = ? WHERE id = ?', [(string)$cat['name'], (int)$a]) > 0) {
                screen($chat, $mid, '✅ نوع سرویس را انتخاب کنید:', ik([
                    [cb('⭐ استارز', 'settype,' . (int)$a . ',stars'), cb('👑 پرمیوم', 'settype,' . (int)$a . ',permium')],
                    [cb('🎁 گیفت استارزی', 'settype,' . (int)$a . ',gift'), cb('🚀 بوست کانال و گروه', 'settype,' . (int)$a . ',boost')],
                ]));
            } else {
                $ans = ['❌ مورد یافت نشد', true];
            }
            break;
        case 'settype':
            $type = in_array($b, ['permium', 'gift', 'boost'], true) ? $b : 'stars';
            if (Db::exec('UPDATE ProductsF SET startsorpermium = ? WHERE id = ?', [$type, (int)$a]) > 0) {
                $labels = ['stars' => '⭐ نوع: استارز', 'permium' => '👑 نوع: پرمیوم', 'gift' => '🎁 نوع: گیفت استارزی', 'boost' => '🚀 نوع: بوست کانال و گروه'];
                Tg::edit($chat, $mid, $labels[$type]);
                if ($type === 'gift') {
                    $btns = [];
                    foreach (GIFTS as $gid => $g) {
                        $btns[] = cb($g['icon'] . ' ' . $g['name'] . ' (' . $g['stars'] . '⭐)', 'gsel,' . (int)$a . ',' . $gid);
                    }
                    Tg::send($chat, '🎁 کدام گیفت را می‌فروشید؟', ik(array_chunk($btns, 2)));
                } elseif ($type === 'boost') {
                    Tg::send($chat, '🚀 مدت بوست را انتخاب کنید:', ik([
                        [cb(BOOSTS['s']['name'], 'bkind,' . (int)$a . ',s')],
                        [cb(BOOSTS['l']['name'], 'bkind,' . (int)$a . ',l')],
                    ]));
                } else {
                    prompt(
                        $chat,
                        'sub_num,' . (int)$a,
                        $type === 'stars' ? 'تعداد استارزی که میخواهید ارسال شود را وارد کنید' : 'مدت اشتراک پرمیوم را به ماه وارد کنید (مثلا 3)'
                    );
                }
            } else {
                $ans = ['❌ مورد یافت نشد', true];
            }
            break;
        case 'gsel':
            $gp = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$a]);
            if (!$gp || p_type($gp) !== 'gift' || !isset(GIFTS[(int)$b])) {
                $ans = ['❌ مورد یافت نشد', true];
                break;
            }
            Db::exec('UPDATE ProductsF SET number = ? WHERE id = ?', [(string)(int)$b, (int)$a]);
            p_autoname((int)$a);
            Tg::edit($chat, $mid, '🎁 گیفت: ' . GIFTS[(int)$b]['icon'] . ' ' . GIFTS[(int)$b]['name']);
            price_offer($chat, Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$a]));
            break;
        case 'bkind':
            $bp = Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$a]);
            if (!$bp || p_type($bp) !== 'boost' || !isset(BOOSTS[$b])) {
                $ans = ['❌ مورد یافت نشد', true];
                break;
            }
            Db::exec('UPDATE ProductsF SET number = ? WHERE id = ?', [(string)BOOSTS[$b]['number'], (int)$a]);
            p_autoname((int)$a);
            Tg::edit($chat, $mid, '🚀 مدت: ' . BOOSTS[$b]['name']);
            price_offer($chat, Db::row('SELECT * FROM ProductsF WHERE id = ?', [(int)$a]));
            break;
        case 'gpr':
            $ans = price_pick($chat, (int)$a, $b);
            break;
        case 'gf':
            $ans = gf_action($chat, $mid, $a, $b);
            break;
        case 'bp':
            $ans = bp_action($chat, $mid, $a, $b);
            break;
        case 'em':
            $ans = em_action($chat, $mid, $a);
            break;
        case 'kya':
            $ans = kya_action($chat, $mid, $uid, $a, $b);
            break;
        case 'kyc':
            $ans = kyc_start($chat, $uid);
            break;
        case 'bo':
            $ans = boost_confirm($chat, $mid, $uid, $user, $a);
            break;

        case 'set_start':
            prompt($chat, 'set_start', "📝 متن استارت را ارسال کنید\n(HTML پشتیبانی می‌شود)\n\nبرای برگشت به متن پیش‌فرض " . BRAND . " فقط «-» بفرستید.");
            break;
        case 'set_help':
            prompt($chat, 'set_help', "📝 متن راهنما را ارسال کنید\n\nبرای برگشت به متن پیش‌فرض فقط «-» بفرستید.");
            break;
        case 'set_rules':
            prompt($chat, 'set_rules', "📝 متن قوانین را ارسال کنید\n\nبرای برگشت به متن پیش‌فرض فقط «-» بفرستید.");
            break;
        case 'adm':
            $ans = adm_action($chat, $mid, $uid, $a, $b);
            break;
        case 'fj':
            $ans = fj_action($chat, $mid, $a, $b);
            break;
        case 'gw':
            $ans = gw_action($chat, $mid, $a);
            break;
        case 'cd':
            $ans = cd_action($chat, $mid, $a);
            break;
        case 'wl':
            $ans = wl_action($chat, $mid, $a, $b);
            break;
        case 'rt':
            $ans = rt_action($chat, $mid, $a, $b, $user);
            break;
        case 'sp':
            $ans = sp_action($chat, $mid, $a, $b);
            break;
        case 'pm':
            $ans = pm_action($chat, $mid, $a, $b);
            break;
        case 'pr_auto':
        case 'pr_manual':
            $ans = pr_choose($chat, (int)$a, $cmd === 'pr_auto');
            break;
        case 'menu':
            if ($a === 'settings') {
                admin_settings_menu($chat, $mid);
            } else {
                admin_toggle_menu($chat, $mid, $a);
            }
            break;
        case 'tg':
            $group = admin_toggle($a);
            if ($group !== null) {
                admin_toggle_menu($chat, $mid, $group);
            }
            break;
    }
    Tg::answer($cbid, $ans[0] ?? '', (bool)($ans[1] ?? false));
}

function handle_update(array $u): void
{
    if (isset($u['callback_query']) && is_array($u['callback_query'])) {
        on_callback($u['callback_query']);
    } elseif (isset($u['message']) && is_array($u['message'])) {
        on_message($u['message']);
    }
}

/* ======================================================================
 *  Web layer
 * ==================================================================== */

function respond_early(string $body = 'ok'): void
{
    ignore_user_abort(true);
    @set_time_limit(0);
    if (!headers_sent()) {
        header('Content-Type: text/plain; charset=utf-8');
        header('Content-Length: ' . strlen($body));
        header('Connection: close');
    }
    echo $body;
    while (ob_get_level() > 0) {
        @ob_end_flush();
    }
    flush();
    if (function_exists('fastcgi_finish_request')) {
        fastcgi_finish_request();
    }
}

function seen_update(int $id): bool
{
    if ($id <= 0) {
        return false;
    }
    $fh = @fopen(Config::$dataDir . '/.updates', 'c+');
    if (!$fh) {
        return false;
    }
    flock($fh, LOCK_EX);
    $ids = json_decode((string)stream_get_contents($fh), true);
    if (!is_array($ids)) {
        $ids = [];
    }
    $seen = in_array($id, $ids, true);
    if (!$seen) {
        $ids[] = $id;
        $ids   = array_slice($ids, -300);
        ftruncate($fh, 0);
        rewind($fh);
        fwrite($fh, json_encode($ids));
        fflush($fh);
    }
    flock($fh, LOCK_UN);
    fclose($fh);
    return $seen;
}

function route_webhook(): void
{
    if (Config::$token === '') {
        http_response_code(503);
        exit('BOT_TOKEN is not set');
    }
    $given = (string)($_SERVER['HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'] ?? '');
    if (!hash_equals(webhook_secret(), $given)) {
        http_response_code(403);
        exit('forbidden');
    }
    $update = json_decode((string)file_get_contents('php://input'), true);
    respond_early();
    if (!is_array($update) || seen_update((int)($update['update_id'] ?? 0))) {
        return;
    }
    try {
        handle_update($update);
    } catch (Throwable $e) {
        logx('update failed: ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
    }
}

function page(int $code, string $title, string $msg, bool $ok = false)
{
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    $bot  = Config::$token !== '' ? bot_username() : '';
    $link = $bot !== '' ? '<a class="btn" href="https://t.me/' . h($bot) . '">بازگشت به ربات</a>' : '';
    $col  = $ok ? '#16a34a' : '#dc2626';
    echo '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        . '<meta name="viewport" content="width=device-width,initial-scale=1"><title>' . h($title) . '</title>'
        . '<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0f172a;font-family:Tahoma,Arial,sans-serif;color:#e2e8f0}'
        . '.c{background:#1e293b;border-radius:18px;padding:36px 28px;max-width:420px;width:88%;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,.4)}'
        . '.i{width:68px;height:68px;border-radius:50%;background:' . $col . ';margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-size:34px;color:#fff}'
        . 'h1{font-size:20px;margin:0 0 10px}p{line-height:1.9;color:#94a3b8;margin:0 0 22px}'
        . '.btn{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:11px 26px;border-radius:10px}</style></head>'
        . '<body><div class="c"><div class="i">' . ($ok ? '✓' : '✕') . '</div><h1>' . h($title) . '</h1><p>' . $msg . '</p>' . $link . '</div></body></html>';
    exit;
}

function route_pay_create(): void
{
    $uid    = (int)($_GET['uid'] ?? 0);
    $amount = (int)($_GET['amount'] ?? 0);
    $t      = (int)($_GET['t'] ?? 0);
    $sig    = (string)($_GET['sig'] ?? '');

    if ($uid <= 0 || !hash_equals(pay_sig($uid, $amount, $t), $sig) || abs(time() - $t) > 3600) {
        page(400, 'لینک نامعتبر', 'این لینک پرداخت نامعتبر یا منقضی شده است. دوباره از داخل ربات اقدام کنید.');
    }
    if ($amount < min_topup() || $amount > max_topup() || !user_exists($uid)) {
        page(400, 'درخواست نامعتبر', 'مبلغ یا کاربر نامعتبر است.');
    }
    $key  = trim((string)Db::setting()['idpay_merchant']);
    $base = base_url();
    if (($key === '') || ((Db::setting()['idpay'] ?? 'on') !== 'on') || $base === '') {
        page(500, 'درگاه غیرفعال', 'درگاه پرداخت در حال حاضر فعال نیست.');
    }
    $r = http_json('https://api.idpay.ir/v1.1/payment', [
        'order_id' => $uid . '-' . time() . random_int(100, 999),
        'amount'   => $amount * 10,
        'desc'     => 'افزایش موجودی ربات',
        'callback' => $base . '/pay/back',
    ], ['X-API-KEY: ' . $key, 'X-SANDBOX: ' . (idpay_sandbox() ? '1' : '0')]);

    $j = $r['json'] ?? null;
    if (!is_array($j)) {
        page(502, 'خطای درگاه', 'ارتباط با درگاه پرداخت برقرار نشد. کمی بعد دوباره تلاش کنید.');
    }
    if (!empty($j['link'])) {
        header('Location: ' . $j['link']);
        exit;
    }
    if (!empty($j['id'])) {
        header('Location: https://idpay.ir/p/' . rawurlencode((string)$j['id']));
        exit;
    }
    $err = $j['error_message'] ?? ($j['error']['message'] ?? 'خطا در ایجاد تراکنش');
    logx('idpay create failed: ' . json_encode($j, JSON_UNESCAPED_UNICODE));
    page(502, 'خطا در ایجاد تراکنش', h((string)$err));
}

function route_pay_back(): void
{
    $in      = $_POST + $_GET;
    $status  = (int)($in['status'] ?? 0);
    $idpayId = (string)($in['id'] ?? '');
    $orderId = (string)($in['order_id'] ?? '');

    if ($idpayId === '' || $orderId === '') {
        page(400, 'اطلاعات ناقص', 'اطلاعات پرداخت ناقص است.');
    }
    if ($status !== 10) {
        page(200, 'پرداخت انجام نشد', 'پرداخت انجام نشد یا لغو شد.');
    }
    $key = trim((string)Db::setting()['idpay_merchant']);
    $r   = http_json('https://api.idpay.ir/v1.1/payment/verify', ['id' => $idpayId, 'order_id' => $orderId], [
        'X-API-KEY: ' . $key,
        'X-SANDBOX: ' . (idpay_sandbox() ? '1' : '0'),
    ]);
    $j = $r['json'] ?? null;
    if (!is_array($j)) {
        page(502, 'خطا در تایید', 'تایید پرداخت با خطا مواجه شد. اگر مبلغ از حساب شما کسر شده با پشتیبانی تماس بگیرید.');
    }
    $st = (int)($j['status'] ?? 0);
    if ($st === 101) {
        page(200, 'پرداخت قبلاً تایید شده', 'این پرداخت قبلاً تایید و به حساب شما اضافه شده است.', true);
    }
    if ($st !== 100) {
        page(200, 'تایید ناموفق', 'تایید پرداخت ناموفق بود.');
    }
    $oid   = (string)($j['order_id'] ?? $orderId);
    $uid   = (int)explode('-', $oid)[0];
    $toman = intdiv((int)($j['amount'] ?? 0), 10);
    if ($uid > 0 && $toman > 0 && user_exists($uid)) {
        coin_add($uid, $toman);
        Tg::send($uid, "✅ پرداخت شما با موفقیت انجام شد.\n💰 مبلغ " . money($toman) . " تومان به موجودی شما اضافه شد.\n🔖 کد رهگیری: <code>" . h($j['track_id'] ?? '') . '</code>');
        notify_admins("💳 پرداخت درگاه موفق\n👤 کاربر: <code>" . $uid . "</code>\n💰 " . money($toman) . ' تومان');
    } else {
        logx("idpay verified but user/amount invalid: $oid");
    }
    page(200, 'پرداخت موفق', 'پرداخت با موفقیت انجام شد.<br>کد رهگیری: ' . h($j['track_id'] ?? ''), true);
}

function route_health(): void
{
    header('Content-Type: application/json; charset=utf-8');
    $db = true;
    try {
        Db::pdo();
    } catch (Throwable $e) {
        $db = false;
        http_response_code(500);
    }
    echo json_encode([
        'ok'      => $db,
        'bot'     => Config::$token !== '',
        'admin'   => count(Config::$admins) > 0,
        'db'      => $db,
        'webhook' => env_base_url() !== '' ? 'auto' : 'manual',
    ]);
    exit;
}

function route(): void
{
    $path   = '/' . trim((string)parse_url((string)($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH), '/');
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

    if ($path === '/webhook' || ($path === '/' && $method === 'POST')) {
        route_webhook();
        return;
    }
    switch ($path) {
        case '/health':
            ensure_webhook();
            route_health();
            break;
        case '/pay':
        case '/pay/index.php':
            route_pay_create();
            break;
        case '/pay/back':
        case '/pay/back.php':
        case '/callback':
            route_pay_back();
            break;
        case '/setwebhook':
            header('Content-Type: application/json; charset=utf-8');
            if (!hash_equals(Config::$token, (string)($_GET['token'] ?? ''))) {
                http_response_code(403);
                echo json_encode(['ok' => false, 'error' => 'pass ?token=BOT_TOKEN']);
                break;
            }
            $b = base_url();
            echo json_encode($b === '' ? ['ok' => false, 'error' => 'base url unknown'] : set_webhook($b));
            break;
        case '/':
            ensure_webhook();
            header('Content-Type: text/html; charset=utf-8');
            echo '<!doctype html><meta charset="utf-8"><title>Bot</title><body style="font-family:sans-serif;text-align:center;padding:60px">✅ Bot is running</body>';
            break;
        default:
            http_response_code(404);
            echo 'Not found';
    }
}

/* ======================================================================
 *  CLI boot (runs once on container start)
 * ==================================================================== */

function cli_boot(): void
{
    try {
        Db::pdo();
        echo '[boot] database ready: ' . Config::$dbPath . "\n";
    } catch (Throwable $e) {
        echo '[boot] database error: ' . $e->getMessage() . "\n";
        exit(1);
    }
    if (Config::$token === '') {
        echo "[boot] WARNING: BOT_TOKEN is not set\n";
        return;
    }
    if (!Config::$admins) {
        echo "[boot] WARNING: ADMIN_ID is not set\n";
    }
    $me = Tg::call('getMe', [], 10);
    if (empty($me['ok'])) {
        echo "[boot] WARNING: BOT_TOKEN rejected by Telegram\n";
        return;
    }
    echo '[boot] bot: @' . ($me['result']['username'] ?? '?') . "\n";
    @file_put_contents(Config::$dataDir . '/.botname', (string)($me['result']['username'] ?? ''));
    brand_sync();
    echo '[boot] branding: ' . BRAND . (Db::kv('brand_v', '') === '2' ? " (synced)\n" : " (will retry on next boot)\n");

    $base = env_base_url();
    if ($base === '') {
        echo "[boot] public domain unknown: generate a Railway domain, then open https://YOUR-DOMAIN/ once (webhook is set automatically)\n";
        return;
    }
    $r = set_webhook($base);
    echo '[boot] webhook ' . ($r['ok'] ? 'set: ' : 'FAILED: ') . $r['url'] . ' ' . $r['description'] . "\n";
}

/* ======================================================================
 *  Entry point
 * ==================================================================== */

Config::load();

if (PHP_SAPI === 'cli') {
    $task = $argv[1] ?? 'boot';
    if ($task === 'boot') {
        cli_boot();
    } elseif ($task === 'tick') {
        cron_tick();
    }
    exit(0);
}

try {
    route();
} catch (Throwable $e) {
    logx('fatal: ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
    if (!headers_sent()) {
        http_response_code(500);
    }
    echo 'error';
}
