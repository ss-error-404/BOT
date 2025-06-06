import os
import json
import random
import asyncio
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext

# === CONFIGURATION ===
TOKEN = "7581984748:AAHFpt58bRtaMp2oWJyS3L02SLDohbxjwT8"
ADMIN_ID = 5814450434
KEYS_FILE = "keys.json"
USED_ACCOUNTS_FILE = "used_accounts.txt"
DATABASE_FILES = ["logs1.txt", "logs2.txt", "logs3.txt", "logs4.txt", "logs5.txt", "logs6.txt"]
DOMAINS = ["100082", "mtacc", "netflix", "tiktok", "roblox"]

# === INIT ===
if not os.path.exists(USED_ACCOUNTS_FILE):
    open(USED_ACCOUNTS_FILE, "w").close()

def load_keys():
    return json.load(open(KEYS_FILE, "r", encoding="utf-8")) if os.path.exists(KEYS_FILE) else {"keys": {}, "user_keys": {}}

def save_keys(data):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

keys_data = load_keys()

def check_user_access(chat_id):
    if chat_id not in keys_data["user_keys"]:
        return False
    expiry = keys_data["user_keys"][chat_id]
    if expiry is not None and datetime.now().timestamp() > expiry:
        del keys_data["user_keys"][chat_id]
        save_keys(keys_data)
        return False
    return True

def remove_url_and_keep_user_pass(line):
    match = re.search(r'([^:]+:[^:]+)$', line.strip())
    return match.group(1) if match else None

# === BOT COMMANDS ===
async def genkey(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ Not authorized!")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /genkey <1h|1d|lifetime>")
    duration = context.args[0]
    key = "KEY-" + ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
    expiry = None if duration == "lifetime" else (datetime.now() + timedelta(hours=int(duration.replace("h", "").replace("d", "") if "h" in duration or "d" in duration else 1))).timestamp()
    keys_data["keys"][key] = expiry
    save_keys(keys_data)
    await update.message.reply_text(f"Generated Key: `{key}`\nDuration: {duration}", parse_mode="Markdown")

async def redeem(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /redeem <key>")
    key = context.args[0]
    if key not in keys_data["keys"]:
        return await update.message.reply_text("âŒ Invalid key.")
    keys_data["user_keys"][chat_id] = keys_data["keys"][key]
    del keys_data["keys"][key]
    save_keys(keys_data)
    await update.message.reply_text("âœ… Key redeemed successfully.")

async def help_command(update: Update, context: CallbackContext):
    text = (
        "*User Commands:*"
        "/redeem <key> - Redeem a key"
        "/status - Check your key"
        "/search <domain> <lines> - Search dump"
        "*Admin Commands:*"
        "/genkey <1h|1d|lifetime>"
        "/revoke <user_id>"
        "/extend <user_id> <1h|1d|lifetime>"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def status(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ Invalid or expired key.")
    expiry = keys_data["user_keys"][chat_id]
    if expiry is None:
        return await update.message.reply_text("âœ… Lifetime access.")
    dt = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"â³ Expires on: {dt}")

async def revoke(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ Not authorized.")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /revoke <user_id>")
    user_id = context.args[0]
    if user_id in keys_data["user_keys"]:
        del keys_data["user_keys"][user_id]
        save_keys(keys_data)
        await update.message.reply_text("âœ… User key revoked.")
    else:
        await update.message.reply_text("âŒ No key found for user.")

async def extend(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ Not authorized.")
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /extend <user_id> <1h|1d|lifetime>")
    user_id, duration = context.args
    if user_id not in keys_data["user_keys"]:
        return await update.message.reply_text("âŒ User has no key.")
    expiry = None if duration == "lifetime" else (datetime.now() + timedelta(hours=int(duration.replace("h", "").replace("d", "") if "h" in duration or "d" in duration else 1))).timestamp()
    keys_data["user_keys"][user_id] = expiry
    save_keys(keys_data)
    await update.message.reply_text("âœ… Key extended.")

async def search_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ Kailangan mo ng valid na key, gago!")
    if len(context.args) < 1:
        return await update.message.reply_text("âš  Usage: /search <domain> <lines>")
    domain = context.args[0]
    try:
        lines_to_send = int(context.args[1]) if len(context.args) > 1 else 10
    except:
        lines_to_send = 10
    found = []
    used = set(open(USED_ACCOUNTS_FILE).read().splitlines())
    for db in DATABASE_FILES:
        if os.path.exists(db):
            with open(db, "r") as f:
                for line in f:
                    if domain in line and line.strip() not in used:
                        cred = remove_url_and_keep_user_pass(line)
                        if cred:
                            found.append(cred)
                        if len(found) >= lines_to_send:
                            break
    if not found:
        return await update.message.reply_text("âœ… No new results found.")
    with open(USED_ACCOUNTS_FILE, "a") as f:
        f.writelines([line + "" for line in found])
    fn = f"search_{domain}.txt"
    with open(fn, "w") as f:
        f.write("".join(found))
    await update.message.reply_document(document=InputFile(fn))
    os.remove(fn)

# === START BOT ===
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("extend", extend))
    app.add_handler(CommandHandler("search", search_command))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
