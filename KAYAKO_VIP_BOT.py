import os
import json
import random
import asyncio
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# === CONFIGURATION ===
TOKEN = "7334052640:AAHvH13WuDkEOGy2ORqfimM1pYXOHAQkzP0"
ADMIN_ID = 5814450434
KEYS_FILE = "keys.json"
DATABASE_FILES = ["logs1.txt", "logs2.txt", "logs3.txt", "logs4.txt", "logs5.txt", "logs6.txt"]
USED_ACCOUNTS_FILE = "used_accounts.txt"
LINES_TO_SEND = 100

# === DOMAIN LIST ===
DOMAINS = [
    "100082", "mtacc", "garena", "roblox", "gaslite", "netflix", "spotify", "tiktok", "pubg", "steam", "facebook",
    "genshin", "instagram", "freefire", "disneyplus", "pornhub", "vivamax", "authgop", "8ball", "crossfire", "paypal",
    "onlyfans", "hulu", "telegram", "warzone", "discord", "linkedin", "microsoft", "yahoo", "gmail", "crypto",
    "binance", "visa", "coinbase", "hotmail", "twitch", "playstation", "nintendo", "xbox", "uber", "airbnb"
]

# === LOAD DATABASE ===
if not os.path.exists(USED_ACCOUNTS_FILE):
    open(USED_ACCOUNTS_FILE, "w").close()

def load_keys():
    return json.load(open(KEYS_FILE, "r", encoding="utf-8")) if os.path.exists(KEYS_FILE) else {"keys": {}, "user_keys": {}, "logs": {}}

def save_keys(data):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

keys_data = load_keys()

# === URL REMOVER FUNCTION ===
def remove_url_and_keep_user_pass(line):
    match = re.search(r'([^:]+:[^:]+)$', line.strip())
    return match.group(1) if match else None

# === CHECK USER ACCESS ===
def check_user_access(chat_id):
    if chat_id not in keys_data["user_keys"]:
        return False

    expiry = keys_data["user_keys"][chat_id]
    if expiry is not None and datetime.now().timestamp() > expiry:
        del keys_data["user_keys"][chat_id]
        save_keys(keys_data)
        return False

    return True

# === /SEARCH COMMAND ===
async def search_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ Kailangan mo ng valid na key, gago!")

    if len(context.args) < 1:
        return await update.message.reply_text("âš  Usage: /search <domain> <lines>
Example: /search 100082 10")

    selected_domain = context.args[0].lower()
    try:
        lines_to_send = int(context.args[1]) if len(context.args) > 1 else 10
    except ValueError:
        return await update.message.reply_text("âŒ Invalid number of lines. Gamitin mo nang tama, gago!")

    processing_msg = await update.message.reply_text("âš¡ *Pinoproseso...mag intay ka,gago!*", parse_mode="Markdown")

    try:
        with open(USED_ACCOUNTS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            used_accounts = set(f.read().splitlines())
    except:
        used_accounts = set()

    matched_lines = []
    raw_lines_to_append = []

    for db_file in DATABASE_FILES:
        if len(matched_lines) >= lines_to_send:
            break
        try:
            with open(db_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped_line = line.strip()
                    if selected_domain in stripped_line.lower() and stripped_line not in used_accounts:
                        cleaned_line = remove_url_and_keep_user_pass(stripped_line)
                        if cleaned_line:
                            matched_lines.append(cleaned_line)
                            raw_lines_to_append.append(stripped_line)
                            if len(matched_lines) >= lines_to_send:
                                break
        except:
            continue

    if not matched_lines:
        return await processing_msg.edit_text(f"âœ… No new results found for '{selected_domain}', you've seen all matches.")

    with open(USED_ACCOUNTS_FILE, "a", encoding="utf-8", errors="ignore") as f:
        f.write("
".join(raw_lines_to_append) + "
")

    filename = f"Search_{selected_domain}.txt"
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.write("
".join(matched_lines))

    await asyncio.sleep(1)
    await processing_msg.delete()

    try:
        with open(filename, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=filename))
    except Exception as e:
        return await update.message.reply_text(f"Error sending file: {str(e)}")

    os.remove(filename)

# === BOT SETUP ===
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("search", search_command))
    print("ðŸ¤– Bot is running FAST...")
    app.run_polling()

if __name__ == "__main__":
    main()
