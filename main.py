import telebot
import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

# ✅ Load environment variables from `.env` file
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# ✅ Validate ADMIN_ID
if not TOKEN:
    raise ValueError("🚨 ERROR: TOKEN is missing! Check your .env file.")
if not ADMIN_ID or not ADMIN_ID.isdigit():
    raise ValueError(
        "🚨 ERROR: ADMIN_ID is missing or invalid! Check your .env file.")
ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ✅ Data Storage (Temporary)
user_points = {}
user_referrals = {}

# ✅ Exchange Rates
PAWS_TO_USDT = 0.001
USDT_TO_INR = 82.5
APP_LINK = "https://shorturl.at/A3o7u"

# ✅ Anti-Spam System
user_last_message = {}


def is_spam(user_id, message_text):
    """Check if the user is sending duplicate messages to prevent spam."""
    last_msg = user_last_message.get(user_id, "")
    user_last_message[user_id] = message_text.strip().lower()
    return last_msg == message_text.strip().lower()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_points:
        user_points[user_id] = 0
        user_referrals[user_id] = 0

    bot.send_message(
        user_id,
        f"👋 **Swagat Hai!** \n\n📲 **App ko install karein aur Paws kamaayein:** {APP_LINK}"
    )


@bot.message_handler(commands=['withdraw'])
def withdraw_paws(message):
    user_id = message.chat.id
    if is_spam(user_id, message.text):
        return bot.send_message(
            user_id, "⚠️ **Spam detected! Kripya firse koshish karein.**")

    bot.send_message(
        user_id,
        "🔹 **Aap kitne Paws withdraw karna chahte hain?**\n(Min: 200, Max: 10,000)"
    )
    bot.register_next_step_handler(message, process_withdraw)


def process_withdraw(message):
    try:
        amount = int(message.text.strip())
        if 200 <= amount <= 10000:
            bot.send_message(
                message.chat.id,
                "💰 **Apna Paws Address bhejein:**\n(Ex: `/pawsaddress XYZ123`)"
            )
            bot.register_next_step_handler(
                message, lambda msg: confirm_withdraw(msg, amount))
        else:
            bot.send_message(message.chat.id,
                             "❌ **Invalid range! Use 200-10,000 Paws.**")
    except ValueError:
        bot.send_message(message.chat.id, "❌ **Please enter a valid number!**")


def confirm_withdraw(message, amount):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            raise ValueError("Invalid format")

        paws_address = parts[1]
        bot.send_message(
            message.chat.id,
            f"✅ **Withdraw Request Sent:**\nAmount: {amount} Paws\nWallet: {paws_address}"
        )
        bot.send_message(
            ADMIN_ID,
            f"📩 **New Withdraw Request!**\nUser: `{message.chat.id}`\nAmount: {amount} Paws\nWallet: {paws_address}"
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ **Galat format!** Kripya `/pawsaddress XYZ123` jaisa format use karein."
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 Error: {str(e)}")


# ✅ Flask Web Server for Webhook
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is Running!"


@app.route(f'/{TOKEN}', methods=['POST'])
def receive_update():
    try:
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print("🚨 Error processing update:", str(e))
        return "ERROR", 500


# ✅ Set Webhook Dynamically with Validation
def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url:
        print(
            "❌ ERROR: Render URL is missing! Set RENDER_EXTERNAL_URL in .env.")
        return

    webhook_url = f"{render_url}/{TOKEN}"
    response = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook",
                             json={"url": webhook_url})

    if response.status_code == 200:
        print("✅ Webhook successfully set:", response.json())
    else:
        print("❌ Webhook failed:", response.json())


# ✅ Run Flask with Gunicorn on Render
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT",
                              10000))  # Default to 10000 if PORT is not set
    app.run(host="0.0.0.0", port=port)
