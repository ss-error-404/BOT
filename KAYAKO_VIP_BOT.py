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
    match = re.search(r'([^:]+:[^:]+)$', line.strip())  # Extract only username:password
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

# === GENERATE MENU ===
async def generate_menu(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ Kailangan mo ng valid na key, gago!")

    keyboard = [[InlineKeyboardButton(domain, callback_data=f"generate_{domain}")] for domain in DOMAINS]
    await update.message.reply_text("ðŸ›  *Pumili ka, gago!*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# === /SEARCH COMMAND ===
async def search_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ Kailangan mo ng valid na key, gago!")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠ Usage: /search <domain> <lines>")
        return await update.message.reply_text("⚠ Usage: /search <domain> <lines>\nExample: /search 100082 10")

    selected_domain = context.args[0].lower()
    try:
        lines_to_send = int(context.args[1]) if len(context.args) > 1 else 10
    except ValueError:
        return await update.message.reply_text("âŒ Invalid number of lines. Gamitin mo nang tama, gago!")

    processing_msg = await update.message.reply_text("âš¡ *Pinoproseso...mag intay ka, gago!*", parse_mode="Markdown")

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
        f.writelines("
".join(raw_lines_to_append) + "
")

    filename = f"Search {selected_domain}.txt"
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.writelines("
".join(matched_lines))

    await asyncio.sleep(1)
    await processing_msg.delete()

    try:
        with open(filename, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=filename))
    except Exception as e:
        return await update.message.reply_text(f"Error sending file: {str(e)}")

    os.remove(filename)


# === /GENKEY COMMAND ===
async def generate_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ You are not authorized to generate keys!")

    if len(context.args) != 1 or context.args[0] not in ["1m", "5m", "1h", "1d", "3d", "7d", "lifetime"]:
        return await update.message.reply_text("âš  Usage: /genkey <duration>\nExample: /genkey 1h")

    duration = context.args[0]
    new_key = "Med-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=7))
    expiry = None if duration == "lifetime" else (datetime.now() + timedelta(seconds={"1m": 60, "5m": 300, "1h": 3600, "1d": 86400, "3d": 259200, "7d": 604800}[duration])).timestamp()

    keys_data["keys"][new_key] = expiry
    save_keys(keys_data)

    await update.message.reply_text(f"âœ… Key generated!\nðŸ”‘ Key: `{new_key}`\nâ³ Expires: `{duration}`", parse_mode="Markdown")

# === /REDEEM KEY ===
async def redeem(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if len(context.args) != 1:
        return await update.message.reply_text("âš  Usage: /redeem <your_key>")

    entered_key = context.args[0]

    if entered_key not in keys_data["keys"]:
        return await update.message.reply_text("âŒ Invalid key!")

    expiry = keys_data["keys"][entered_key]
    if expiry is not None and datetime.now().timestamp() > expiry:
        del keys_data["keys"][entered_key]
        save_keys(keys_data)
        return await update.message.reply_text("âŒ Key has expired!")

    keys_data["user_keys"][chat_id] = expiry
    del keys_data["keys"][entered_key]
    save_keys(keys_data)

    await update.message.reply_text("âœ… Key redeemed. You may now use /search.")

# === /DELETE KEY ===
async def delete_user_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ You are not authorized to delete keys!")

    if len(context.args) != 1:
        return await update.message.reply_text("âš  Usage: /delete <user_id>")

    user_id = context.args[0]

    if user_id not in keys_data["user_keys"]:
        return await update.message.reply_text("âŒ No active key found for that user.")

    del keys_data["user_keys"][user_id]
    save_keys(keys_data)

    await update.message.reply_text(f"âœ… Key deleted for user `{user_id}`.", parse_mode="Markdown")

# === /EXTEND KEY ===
async def extend_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("âŒ You are not authorized to extend keys!")

    if len(context.args) != 2:
        return await update.message.reply_text("âš  Usage: /extend <user_id> <duration>")

    user_id, duration = context.args
    if user_id not in keys_data["user_keys"]:
        return await update.message.reply_text("âŒ No active key found for that user.")

    if duration not in ["1m", "5m", "1h", "1d", "3d", "7d", "lifetime"]:
        return await update.message.reply_text("âš  Invalid duration. Use: 1m, 5m, 1h, 1d, 3d, 7d, lifetime")

    current_expiry = keys_data["user_keys"][user_id]
    now = datetime.now().timestamp()

    if duration == "lifetime":
        new_expiry = None
    else:
        seconds = {"1m": 60, "5m": 300, "1h": 3600, "1d": 86400, "3d": 259200, "7d": 604800}[duration]
        if current_expiry is None:
            return await update.message.reply_text("âŒ Already lifetime access.")
        new_expiry = max(current_expiry, now) + seconds

    keys_data["user_keys"][user_id] = new_expiry
    save_keys(keys_data)

    await update.message.reply_text(f"âœ… Extended key for `{user_id}` by `{duration}`.", parse_mode="Markdown")

# === /STATUS COMMAND ===
async def status(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("âŒ You don't have a valid key!")

    expiry = keys_data["user_keys"].get(chat_id, None)
    if expiry is None:
        return await update.message.reply_text("âœ… Your key has lifetime access.")
    expiration_time = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"â³ Your key expires on: {expiration_time}")

# === /HELP COMMAND ===
async def help_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if chat_id == str(ADMIN_ID):
        help_text = (
            "ðŸ›  *Admin Commands*:
"
            "/genkey <duration>
/delete <user_id>
/extend <user_id> <duration>
"
            "/status
/search <domain>
"
        )
    else:
        help_text = (
            "ðŸ“Œ *User Commands*:
"
            "/redeem <key>
/status
/search <domain>
"
        )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# === /START COMMAND ===
async def start(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    domain_list = "\n".join([f"â€¢ `{domain}`" for domain in DOMAINS])
    message = (
        "ðŸ‘‹ *Welcome to KAYAKO VIP BOT!*

"
        "Here are available domains you can search:

"
        f"{domain_list}

"
        "Use /search <domain> <lines> to proceed."
    )
    await update.message.reply_text(message, parse_mode="Markdown")


# === BOT SETUP ===
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("genkey", generate_key))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("delete", delete_user_key))
    app.add_handler(CommandHandler("extend", extend_key))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_command))
    # The following handlers must exist elsewhere in your code
    # app.add_handler(CommandHandler("genkey", generate_key))
    # app.add_handler(CommandHandler("redeem", redeem))
    # app.add_handler(CommandHandler("delete", delete_user_key))
    # app.add_handler(CommandHandler("extend", extend_key))
    # app.add_handler(CommandHandler("status", status))
    # app.add_handler(CommandHandler("help", help_command))
    # app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_menu))
    print("ðŸ¤– Bot is running FAST...")
    app.run_polling()

if __name__ == "__main__":
    main()
