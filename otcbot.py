import json
import random
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = "8546581264:AAEpFJS3FLY2tqskvLu2kROHOXLYXP8k7JM"
ADMIN_ID = 1657392518

SCAN_INTERVAL = 60
COUNTDOWN_SECONDS = 10
CONFIDENCE_MIN = 88

OTC_PAIRS = [
    "BTC OTC",
    "ETH OTC",
    "BEAM OTC",
    "APTOS OTC",
    "SOLANA OTC",
    "PEPE OTC", 
    "TRUMP OTC",
    "USD/BDT OTC",
    "USD/BRL OTC",
    "USD/INR OTC",
    "USD/MXN OTC",
    "USD/TRY OTC",
    "USD/PHP OTC",
    "NZD/CHF OTC",
    "NZD/JPY OTC",
    "USD/PKR OTC",
    "USD/COP OTC",
    "USD/ARS OTC",
]

USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

# ================= STORAGE =================

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

USER_KEYS = load_json(USERS_FILE)
GENERATED_KEYS = load_json(KEYS_FILE)
LAST_SIGNAL_TIME = {}

# ================= HELPERS =================

def is_pro(uid):
    uid = str(uid)
    return uid in USER_KEYS and datetime.fromisoformat(USER_KEYS[uid]) > datetime.utcnow()

def generate_key(days):
    key = f"OTC-{random.randint(100000,999999)}"
    expiry = datetime.utcnow() + timedelta(days=days)
    GENERATED_KEYS[key] = expiry.isoformat()
    save_json(KEYS_FILE, GENERATED_KEYS)
    return key

# ================= FAKE OTC CANDLES =================

def get_latest_candles(pair):
    base = random.uniform(1.0, 2.0)
    candles = []
    for _ in range(10):   # 🔥 CHANGED FROM 6 TO 10
        o = base + random.uniform(-0.01, 0.01)
        c = o + random.uniform(-0.015, 0.015)
        h = max(o, c) + random.uniform(0.0, 0.01)
        l = min(o, c) - random.uniform(0.0, 0.01)
        candles.append({"open": o, "close": c, "high": h, "low": l})
        base = c
    return candles

# ================= PRICE ACTION ENGINE =================

import random

def analyze_market(candles):

    if len(candles) < 8:
        return None

    # Use CLOSED candles only
    c1 = candles[-2]
    c2 = candles[-3]
    c3 = candles[-4]
    c4 = candles[-5]
    c5 = candles[-6]
    c6 = candles[-7]

    def body(c):
        return abs(c["close"] - c["open"])

    def is_bull(c):
        return c["close"] > c["open"]

    def is_bear(c):
        return c["close"] < c["open"]

    def upper_wick(c):
        return c["high"] - max(c["open"], c["close"])

    def lower_wick(c):
        return min(c["open"], c["close"]) - c["low"]

    # ==========================================================
    # ✅ PATTERN 3 – SIDEWAYS WICK BREAK (SELL)
    # Green → Red → Green (long lower wick) → expect RED
    # ==========================================================
    if (
        is_bull(c4) and
        is_bear(c3) and
        is_bull(c2) and
        lower_wick(c2) > body(c2) * 1.2 and
        is_bear(c1)
    ):
        confidence = 88 + random.randint(0, 5)
        return ("SELL", "Pattern 3 - Sideways Wick Break", confidence)

    # ==========================================================
    # ✅ PATTERN 18 – RESISTANCE REJECT (SELL)
    # Long Red → 3 Green + 1 Red inside range → expect RED
    # ==========================================================
    if (
        is_bear(c6) and body(c6) > body(c5) * 1.5 and
        is_bull(c5) and
        is_bull(c4) and
        is_bull(c3) and
        is_bear(c2) and
        c5["high"] < c6["high"] and
        c4["high"] < c6["high"] and
        c3["high"] < c6["high"] and
        is_bear(c1)
    ):
        confidence = 90 + random.randint(0, 5)
        return ("SELL", "Pattern 18 - Resistance Reject", confidence)

    # ==========================================================
    # ✅ PATTERN 19 – SUPPORT REJECT (BUY)
    # Long Green → 3 Red + 1 Green inside range → expect GREEN
    # ==========================================================
    if (
        is_bull(c6) and body(c6) > body(c5) * 1.5 and
        is_bear(c5) and
        is_bear(c4) and
        is_bear(c3) and
        is_bull(c2) and
        c5["low"] > c6["low"] and
        c4["low"] > c6["low"] and
        c3["low"] > c6["low"] and
        is_bull(c1)
    ):
        confidence = 90 + random.randint(0, 5)
        return ("BUY", "Pattern 19 - Support Reject", confidence)

    # ==========================================================
    # ✅ PATTERN 22 – UPTREND CONTINUATION (BUY)
    # 3 Green + small Red pullback → expect GREEN
    # ==========================================================
    if (
        is_bull(c5) and
        is_bull(c4) and
        is_bull(c3) and
        is_bear(c2) and
        body(c2) < body(c3) and
        is_bull(c1)
    ):
        confidence = 89 + random.randint(0, 5)
        return ("BUY", "Pattern 22 - Uptrend Continuation", confidence)

    # ==========================================================
    # ✅ PATTERN 23 – DOWNTREND CONTINUATION (SELL)
    # 3 Red + small Green pullback → expect RED
    # ==========================================================
    if (
        is_bear(c5) and
        is_bear(c4) and
        is_bear(c3) and
        is_bull(c2) and
        body(c2) < body(c3) and
        is_bear(c1)
    ):
        confidence = 89 + random.randint(0, 5)
        return ("SELL", "Pattern 23 - Downtrend Continuation", confidence)

    # ==========================================================
    # ✅ PATTERN 25 – LONG WICK BULLISH REVERSAL (BUY)
    # Red (long tail) → Green → Green → BUY
    # ==========================================================
    if (
        is_bear(c3) and
        is_bull(c2) and
        is_bull(c1) and
        lower_wick(c3) > upper_wick(c2) * 1.2 and
        lower_wick(c3) > body(c3)
    ):
        confidence = 92 + random.randint(0, 5)
        return ("BUY", "Pattern 25 - Long Wick Bullish", confidence)

    return None


# ================= AUTO SCANNER =================

async def auto_scan_all_pairs(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow().timestamp()

    for pair in OTC_PAIRS:
        if pair in LAST_SIGNAL_TIME and now - LAST_SIGNAL_TIME[pair] < SCAN_INTERVAL:
            continue

        candles = get_latest_candles(pair)
        result = analyze_market(candles)
        if not result:
            continue

        direction, pattern, confidence = result
        if confidence < CONFIDENCE_MIN:
            continue

        LAST_SIGNAL_TIME[pair] = now

        pre_msg = (
            "⏳ *SIGNAL INCOMING*\n"
            f"📊 {pair}\n"
            f"📍 {direction}\n"
            f"🎯 {confidence}%\n"
            f"⏱ Entry in {COUNTDOWN_SECONDS}s"
        )

        for uid in USER_KEYS:
            if is_pro(uid) or int(uid) == ADMIN_ID:
                await context.bot.send_message(uid, pre_msg, parse_mode="Markdown")

        await asyncio.sleep(COUNTDOWN_SECONDS)

       # ENTRY MESSAGE
        entry_msg = (
            "🚀 *ENTER NOW*\n"
            "------------------\n"
            f"📊 Pair: *{pair}*\n"
            f"📍 Direction: *{direction}*\n"
            "⏱ Expiry: *1 Minute*\n"
            "📌 Entry: *ENTER NOW*\n"
            "------------------"
        )

        for uid in USER_KEYS:
            if is_pro(uid) or int(uid) == ADMIN_ID:
                await context.bot.send_message(uid, entry_msg, parse_mode="Markdown")

async def send_manual_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not is_pro(uid) and uid != ADMIN_ID:
        await update.message.reply_text(
            "🔒 This feature is for VIP members only.\n\nActivate subscription first."
        )
        return

    best_signal = None
    best_confidence = 0

    for pair in OTC_PAIRS:
        candles = get_latest_candles(pair)
        result = analyze_market(candles)

        if not result:
            continue

        direction, pattern, confidence = result

        if confidence >= CONFIDENCE_MIN and confidence > best_confidence:
            best_signal = (pair, direction, pattern, confidence)
            best_confidence = confidence

    if not best_signal:
        await update.message.reply_text("⚠️ No strong setup found right now. Try again in 1 minute.")
        return

    pair, direction, pattern, confidence = best_signal

    await update.message.reply_text(
        "🚀 *SIGNAL READY*\n"
        "------------------\n"
        f"📊 Pair: *{pair}*\n"
        f"📍 Direction: *{direction}*\n"
        f"🎯 Confidence: *{confidence}%*\n"
        "⏱ Expiry: *1 Minute*\n"
        "------------------",
        parse_mode="Markdown"
    )

# ================= MENUS =================

def admin_panel():
    return ReplyKeyboardMarkup(
        [
            ["🔑 Generate Key", "👥 Users"],
            ["📡 Get Signal"],
        ],
        resize_keyboard=True,
    )

def user_panel():
    return ReplyKeyboardMarkup(
        [
            ["📡 Get Signal"],
            ["💳 Buy Plan"],
            ["📈 Status"],
        ],
        resize_keyboard=True,
    )

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=admin_panel())
    else:
        await update.message.reply_text(
            "🚀 *OTC VIP SIGNAL BOT*\n\n"
            "⏱ 1-Min OTC Signals\n"
            "📊 Price Action\n"
            "🔐 Key Access",
            parse_mode="Markdown",
            reply_markup=user_panel(),
        )

async def usekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage:\n/usekey YOUR_KEY")
        return

    key = context.args[0]
    uid = str(update.effective_user.id)

    if key not in GENERATED_KEYS:
        await update.message.reply_text("❌ Invalid key")
        return

    USER_KEYS[uid] = GENERATED_KEYS[key]
    del GENERATED_KEYS[key]

    save_json(USERS_FILE, USER_KEYS)
    save_json(KEYS_FILE, GENERATED_KEYS)

    await update.message.reply_text("✅ Subscription activated")


# ================= BUTTONS =================

async def bottom_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # 📡 Manual Signal
    if text == "📡 Get Signal":
        await send_manual_signal(update, context)
        return

    # 👑 Admin Panel Buttons
    if uid == ADMIN_ID:
        if text == "🔑 Generate Key":
            keyboard = [
                [InlineKeyboardButton("30 Days", callback_data="KEY_30"),
                 InlineKeyboardButton("90 Days", callback_data="KEY_90")],
                [InlineKeyboardButton("180 Days", callback_data="KEY_180"),
                 InlineKeyboardButton("365 Days", callback_data="KEY_365")]
            ]
            await update.message.reply_text(
                "🔐 Select subscription duration:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if text == "👥 Users":
            await update.message.reply_text(
                f"👥 Total: {len(USER_KEYS)}"
            )
            return

    # 💳 Buy Plan
    if text == "💳 Buy Plan":
        await update.message.reply_text(
            "💎 *SUBSCRIPTION PLANS*\n\n"
            "30 Days – ₹499\n"
            "90 Days – ₹1299\n"
            "180 Days – ₹2299\n"
            "365 Days – ₹3999\n\n"
            "📩 Contact Admin for payment",
            parse_mode="Markdown"
        )
        return

    # 📈 Status
    if text == "📈 Status":
        if is_pro(uid):
            expiry = datetime.fromisoformat(USER_KEYS[str(uid)])
            await update.message.reply_text(
                f"✅ *Subscription Active*\n\n"
                f"⏱ Valid till: *{expiry.strftime('%d %b %Y')}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ *No active subscription*\n\n"
                "🔑 Please activate a key or buy a plan.",
                parse_mode="Markdown"
            )
        return



# ================= CALLBACKS =================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    plans = {
        "KEY_30": 30,
        "KEY_90": 90,
        "KEY_180": 180,
        "KEY_365": 365,
    }

    if query.data in plans:
        days = plans[query.data]
        key = generate_key(days)

        await query.message.reply_text(
            f"🔑 *Key Generated Successfully*\n\n"
            f"`{key}`\n"
            f"⏱ Valid for *{days} days*",
            parse_mode="Markdown"
        )

# ================= ANNOUNCEMENT COMMAND =================

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/announce YOUR MESSAGE")
        return

    msg = "📢 *ADMIN ANNOUNCEMENT*\n\n" + " ".join(context.args)

    for uid in USER_KEYS:
        await context.bot.send_message(uid, msg, parse_mode="Markdown")

    await update.message.reply_text("✅ Announcement sent to all users")



# ================= MAIN =================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usekey", usekey))
    app.add_handler(CommandHandler("announce", announce))

    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bottom_buttons))

    print("💎 VIP BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
