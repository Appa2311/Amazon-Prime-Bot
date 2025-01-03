from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.error import BadRequest
import json

# Bot Token and Channel ID
BOT_TOKEN = "7645731305:AAHsFxSt0psDpZv-f7dTW4rRIa_fgbSiXIU"
CHANNEL_ID = "@Gaming_Centre_Zone"

# File paths
USER_DATA_FILE = "referral_data.json"
ACCOUNTS_FILE = "accounts.json"

# Load or initialize user data
try:
    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

# Load or initialize accounts data
try:
    with open(ACCOUNTS_FILE, "r") as f:
        accounts_data = json.load(f)
except FileNotFoundError:
    accounts_data = []

# Save user data
def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Save accounts data
def save_accounts_data():
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts_data, f)

# Check if the user has joined the channel
def check_membership(user_id, context):
    try:
        member = context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False

# /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = str(user.id)

    # Check if the user has joined the channel
    if not check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton(f"Join {CHANNEL_ID}", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton("Verify", callback_data="verify")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"Welcome, {user.first_name}! You need to join our channel to use this bot.",
            reply_markup=reply_markup
        )
    else:
        # Initialize user data if not present
        if user_id not in user_data:
            user_data[user_id] = {"points": 0, "referrals": []}
            save_user_data()
        main_menu(update)

# Verify button callback
def verify(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)

    if check_membership(user_id, context):
        query.edit_message_text("Thank you for joining the channel! You can now use the bot.")
        if user_id not in user_data:
            user_data[user_id] = {"points": 0, "referrals": []}
            save_user_data()
        main_menu(update)
    else:
        query.edit_message_text(
            f"You have not joined the channel yet. Please join {CHANNEL_ID} and then click 'Verify'."
        )

# Middleware to check channel membership before processing messages
def membership_guard(update: Update, context: CallbackContext) -> bool:
    user_id = str(update.effective_user.id)
    if not check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton(f"Join {CHANNEL_ID}", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton("Verify", callback_data="verify")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"You are no longer subscribed to {CHANNEL_ID}. Please join the channel and verify again.",
            reply_markup=reply_markup
        )
        return False
    return True

# Show main menu
def main_menu(update: Update) -> None:
    keyboard = [
        ["Prime Withdraw 💰"],
        ["👤 My Account", "📢 Invite Friends"],
        ["Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Handle reply buttons
def reply_handler(update: Update, context: CallbackContext) -> None:
    if not membership_guard(update, context):
        return

    user_id = str(update.effective_user.id)
    text = update.message.text

    if text == "Prime Withdraw 💰":
        prime_withdraw(update, user_id)
    elif text == "👤 My Account":
        points = user_data[user_id]["points"]
        referrals = len(user_data[user_id]["referrals"])
        update.message.reply_text(f"👤 My Account:\n\nPoints: {points}\nReferrals: {referrals}")
    elif text == "📢 Invite Friends":
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        update.message.reply_text(
            f"📢 Invite your friends and earn points!\n\n"
            f"Share this link: {referral_link}\n\n"
            f"1 Referral = 2 Points. Earn 10 Points to claim your prize!"
        )
    elif text == "Help":
        update.message.reply_text("For any help, contact: @Devloper_admin_bot")

# Prime Withdraw functionality
def prime_withdraw(update: Update, user_id: str) -> None:
    if user_data[user_id]["points"] < 5:
        update.message.reply_text("You need at least 5 points to claim an account!")
        return

    # Check for available accounts
    for account in accounts_data:
        if len(account["claimed_by"]) < 5:
            account["claimed_by"].append(user_id)
            save_accounts_data()
            user_data[user_id]["points"] -= 5
            save_user_data()
            update.message.reply_text(
                f"Here is your account:\n\nEmail: {account['account']}\nPassword: {account['password']}\n"
                f"Thank you for claiming your Prime!"
            )
            return

    # Notify admins if no accounts are left
    admins = ["@Developer_2311", "@Owner1d"]
    for admin in admins:
        context.bot.send_message(chat_id=admin, text="All accounts have been claimed. Please add new accounts.")
    update.message.reply_text(
        "No accounts are currently available. Please wait for fresh accounts to be added."
    )

# Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()