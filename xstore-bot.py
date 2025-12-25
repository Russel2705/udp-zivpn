import os, time, random, string, json
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

load_dotenv("/etc/xstore/config.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

QRIS_LINK = open("/etc/xstore/qris_link.txt").read().strip()
DB = "/etc/xstore/users.json"
MANAGER = "/etc/xstore/xstore-manager.sh"
SERVERS_FILE = "/etc/xstore/servers.txt"

users = json.load(open(DB)) if os.path.exists(DB) else {}
SERVERS = {}
PRICES = {}
with open(SERVERS_FILE) as f:
    for line in f:
        if line.strip():
            key, name, ip, price = line.strip().split("|")
            SERVERS[key] = {"name": name, "ip": ip}
            PRICES[key] = int(price)

def save_users(): json.dump(users, open(DB, "w"), indent=4)

def gen_pass(): return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in users:
        users[uid] = {"saldo": 0}
        save_users()
    keyboard = ReplyKeyboardMarkup([
        ["+ Buat Akun", "⏳ Trial Akun"],
        ["💰 TopUp Saldo"]
    ], resize_keyboard=True)
    text = f"XSTORE ZiVPN PREMIUM\nID: {uid}\nSaldo: Rp {users[uid]['saldo']:,}"
    await update.message.reply_text(text, reply_markup=keyboard)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    if text == "+ Buat Akun":
        buttons = [[InlineKeyboardButton(f"{SERVERS[k]['name']} - Rp{PRICES[k]:,}", callback_data=f"beli_{k}")] for k in SERVERS]
        await update.message.reply_text("Pilih server premium 30 hari:", reply_markup=InlineKeyboardMarkup(buttons))
    elif text == "⏳ Trial Akun":
        buttons = [[InlineKeyboardButton(SERVERS[k]['name'], callback_data=f"trial_{k}")] for k in SERVERS]
        await update.message.reply_text("Pilih server trial 3 jam:", reply_markup=InlineKeyboardMarkup(buttons))
    elif text == "💰 TopUp Saldo":
        await update.message.reply_text(f"TopUp via QRIS GoPay:\n[QRIS]({QRIS_LINK})\nKirim bukti screenshot.", parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = str(q.from_user.id)
    if data.startswith("trial_"):
        srv = data[6:]
        pw = gen_pass()
        os.system(f"{MANAGER} --add-password {pw} {srv} trial {uid}")
        await q.edit_message_text(f"Trial {SERVERS[srv]['name']}\nPassword: {pw}\nHost: {SERVERS[srv]['ip']}\nPort: 5667")
    elif data.startswith("beli_"):
        srv = data[5:]
        price = PRICES[srv]
        await q.edit_message_text(f"Premium {SERVERS[srv]['name']} Rp{price:,}\n\nTransfer exact Rp{price:,} via QRIS GoPay:\n[QRIS]({QRIS_LINK})\nKirim bukti screenshot.", parse_mode="Markdown")
        context.user_data["pending"] = {"srv": srv, "uid": uid}

# Bukti transfer foto
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.forward_message(OWNER_ID, update.message.chat_id, update.message.message_id)
    await update.message.reply_text("Bukti diterima. Tunggu confirm admin.")

# Admin confirm & buat akun
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        target_uid = context.args[0]
        srv = context.args[1]
        pw = gen_pass()
        os.system(f"{MANAGER} --add-password {pw} {srv} paid {target_uid}")
        await context.bot.send_message(int(target_uid), f"Premium {SERVERS[srv]['name']} Aktif!\nPassword: {pw}\nHost: {SERVERS[srv]['ip']}\nPort: 5667")
        await update.message.reply_text("Akun dibuat.")
    except:
        await update.message.reply_text("Usage: /confirm <user_id> <server_key>")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("confirm", confirm))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.run_polling()