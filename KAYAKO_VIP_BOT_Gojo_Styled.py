import os
import json
import random
import asyncio
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# === CONFIGURATION ===
TOKEN = ""
ADMIN_ID = 
KEYS_FILE = "keys.json"
DATABASE_FILES = ["logs1.txt", "logs2.txt", "logs3.txt", "logs4.txt", "logs5.txt", "logs6.txt"]
USED_ACCOUNTS_FILE = "used_accounts.txt"
LINES_TO_SEND = 100

# === DOMAIN LIST ===
DOMAINS = [
    "100082", "mtacc", "garena", "roblox", "gaslite", "netflix", "spotify", "tiktok", "pubg", "steam", "facebook", "genshin", "instagram", "freefire", "disneyplus", "pornhub", "vivamax", "authgop", "8ball", "crossfire", "paypal", "onlyfans", "hulu", "telegram", "warzone", "discord", "linkedin", "microsoft", "yahoo", "gmail", "crypto", "binance", "visa", "coinbase", "hotmail", "twitch", "playstation", "nintendo", "xbox", "uber", "airbnb"
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
        del keys_data["user_keys"][chat_id]  # Remove expired key
        save_keys(keys_data)
        return False
    
    return True

# === GENERATE MENU ===
async def generate_menu(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    
    if not check_user_access(chat_id):
        return await update.message.reply_text("❌ Kailangan mo ng valid na key,gago!")

    keyboard = [[InlineKeyboardButton(domain, callback_data=f"generate_{domain}")] for domain in DOMAINS]
    await update.message.reply_text("🛠 **Pumili ka,gago!:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# === /SEARCH COMMAND ===
async def search_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("❌ Kailangan mo ng valid na key, gago!")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠ Usage: /search <domain> <lines>\nExample: /search 100082 10")

    selected_domain = context.args[0].lower()
    try:
        lines_to_send = int(context.args[1]) if len(context.args) > 1 else 10  # Default to 10 lines
    except ValueError:
        return await update.message.reply_text("❌ Invalid number of lines. Gamitin mo nang tama, gago!")

    
    # Track usage
    keys_data['logs'][chat_id] = keys_data['logs'].get(chat_id, 0) + 1
    save_keys(keys_data)

    processing_msg = await update.message.reply_text("⚡ **Pinoproseso...mag intay ka,gago!**")

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
        return await processing_msg.edit_text(f"✅ No new results found for '{selected_domain}', you've seen all matches.")

    with open(USED_ACCOUNTS_FILE, "a", encoding="utf-8", errors="ignore") as f:
        f.writelines("\n".join(raw_lines_to_append) + "\n")

    filename = f"Search {selected_domain}.txt"
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.writelines("\n".join(matched_lines))

    await asyncio.sleep(1)
    await processing_msg.delete()

    try:
        with open(filename, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=filename))
    except Exception as e:
        return await update.message.reply_text(f"Error sending file: {str(e)}")

    os.remove(filename)

# === GENERATE KEY COMMAND ===
async def generate_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("❌ You are not authorized to generate keys!")

    if len(context.args) != 1 or context.args[0] not in ["1m", "5m", "1h", "1d", "3d", "7d", "lifetime"]:
        return await update.message.reply_text("⚠ Usage: `/genkey <duration>`\nExample: `/genkey 1h`", parse_mode="Markdown")

    duration = context.args[0]
    new_key = "Med-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=7))
    expiry = None if duration == "lifetime" else (datetime.now() + timedelta(seconds={"1m": 60, "5m": 300, "1h": 3600, "1d": 86400, "3d": 259200, "7d": 604800}[duration])).timestamp()

    keys_data["keys"][new_key] = expiry
    save_keys(keys_data)

    await update.message.reply_text(f"✅ **Bigay moto sa pogi!**\n🔑 Key: `{new_key}`\n⏳ Expires: `{duration}`", parse_mode="Markdown")

# === REDEEM KEY COMMAND ===
async def redeem(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if len(context.args) != 1:
        return await update.message.reply_text("⚠ Usage: `/redeem <your_key>`", parse_mode="Markdown")

    entered_key = context.args[0]

    if entered_key not in keys_data["keys"]:
        return await update.message.reply_text("❌ Kailangan mo ng valid na key,gago!")

    expiry = keys_data["keys"][entered_key]
    if expiry is not None and datetime.now().timestamp() > expiry:
        del keys_data["keys"][entered_key]
        save_keys(keys_data)
        return await update.message.reply_text("❌ Kailangan mo ng valid na key,gago!")

    keys_data["user_keys"][chat_id] = expiry
    del keys_data["keys"][entered_key]
    save_keys(keys_data)

    await update.message.reply_text("✅ Pinapayagan kana mag /search {domains}.")

# === /DELETE COMMAND (Admin only) ===
async def delete_user_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("❌ Hindi ka authorized gamitin 'to, gago!")

    if len(context.args) != 1:
        return await update.message.reply_text("⚠ Usage: /delete <user_id>")

    user_id = context.args[0]

    if user_id not in keys_data["user_keys"]:
        return await update.message.reply_text("❌ Walang key ang user na 'yan.")

    del keys_data["user_keys"][user_id]
    save_keys(keys_data)

    await update.message.reply_text(f"✅ Nabura na ang key ni user `{user_id}`.", parse_mode="Markdown")

# === /EXTEND COMMAND (Admin only) ===
async def extend_key(update: Update, context: CallbackContext):
    if update.message.chat_id != ADMIN_ID:
        return await update.message.reply_text("❌ Hindi ka authorized gamitin 'to, gago!")

    if len(context.args) != 2:
        return await update.message.reply_text("⚠ Usage: /extend <user_id> <duration>\nHalimbawa: /extend 123456789 5m")

    user_id, duration = context.args
    if user_id not in keys_data["user_keys"]:
        return await update.message.reply_text("❌ Walang active key ang user na 'yan.")

    if duration not in ["1m", "5m", "1h", "1d", "3d", "7d", "lifetime"]:
        return await update.message.reply_text("⚠ Invalid duration. Gamitin ang: 1m, 5m, 1h, 1d, 3d, 7d, lifetime")

    current_expiry = keys_data["user_keys"][user_id]
    now = datetime.now().timestamp()

    if duration == "lifetime":
        new_expiry = None
    else:
        seconds = {"1m": 60, "5m": 300, "1h": 3600, "1d": 86400, "3d": 259200, "7d": 604800}[duration]
        if current_expiry is None:
            return await update.message.reply_text("❌ Lifetime na ang access ng user na 'yan.")
        new_expiry = max(current_expiry, now) + seconds

    keys_data["user_keys"][user_id] = new_expiry
    save_keys(keys_data)

    await update.message.reply_text(f"✅ Na-extend ang key ni `{user_id}` ng `{duration}`.", parse_mode="Markdown")

# === /STATUS COMMAND ===
async def status(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    if not check_user_access(chat_id):
        return await update.message.reply_text("❌ Kailangan mo ng valid na key!")

    # Get the expiration date or status of the key
    expiry = keys_data["user_keys"].get(chat_id, None)

    if expiry is None:
        return await update.message.reply_text("✅ **Lifetime** access ang key mo, walang expiration.")
    
    # Format the expiration time
    expiration_time = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"⏳ **Key Status**\n- **Expires on:** {expiration_time}")

# === /HELP COMMAND ===
async def help_command(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)

    # Check if the user is an admin
    if chat_id == str(ADMIN_ID):
        # Admin help message
        help_text = (
            "🛠 **Admin Commands**:\n"
            "/genkey <duration> - Generate a new key for users\n"
            "/delete <user_id> - Delete a user's key\n"
            "/extend <user_id> <duration> - Extend a user's key\n"
            "/status - View the expiration status of your key\n"
            "/search <domain> - Search logs for a specific domain\n"
            "Example: /search 100082\n"
        )
    else:
        # User help message
        help_text = (
            "🛠 **User Commands**:\n"
            "/status - View the expiration status of your key\n"
            "/search <domain> - Search logs for a specific domain\n"
            "Example: /search 100082\n"
        )

    await update.message.reply_text(help_text, parse_mode="Markdown")




# === /START COMMAND (Gojo Anime Themed) ===
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🔐 Redeem Key", callback_data="key")],
        [InlineKeyboardButton("🌀 Generate", callback_data="generate")],
        [InlineKeyboardButton("💫 Status", callback_data="status")],
        [InlineKeyboardButton("🔍 Search", callback_data="search")],
        [InlineKeyboardButton("🏆 Top Users", callback_data="topusers"), InlineKeyboardButton("📂 Validator", callback_data="validator")],
        [InlineKeyboardButton("🧮 Count Lines", callback_data="countlines"), InlineKeyboardButton("📝 Rename File", callback_data="renamefile")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin")],
        [InlineKeyboardButton("📜 Help", callback_data="help")]
    ]
    banner = (
        "╔═━━━━✦❘༻༺❘✦━━━━═╗
"
        "🌀 *KAYAKO_VIP_BOT* 🌀
"
        "『 Powered by Gojo Satoru 』
"
        "╚═━━━━✦❘༻༺❘✦━━━━═╝

"
        "⚔️ _“Throughout Heaven and Earth, I alone am the honored one.”_
"
        "🔥 Welcome, warrior. Pick your tool and dominate.
"
    )
    await update.message.reply_text(banner, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# === BOT SETUP ===
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("genkey", generate_key))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("delete", delete_user_key))
    app.add_handler(CommandHandler("extend", extend_key))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("topusers", top_users))
    app.add_handler(CommandHandler("validator", validator))
    app.add_handler(CommandHandler("countlines", count_lines))
    app.add_handler(CommandHandler("renamefile", rename_file))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    
    
    print("🤖 Bot is running FAST...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
    
    