import telebot
import os
import threading
import requests
from flask import Flask, request
from dotenv import load_dotenv

# 🔹 `.env` file se environment variables load karein
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN or ADMIN_ID == 0:
    raise ValueError(
        "🚨 ERROR: TOKEN ya ADMIN_ID missing hai! .env file check karein.")

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
    last_msg = user_last_message.get(user_id, "")
    user_last_message[user_id] = message_text
    return last_msg == message_text


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
        amount = int(message.text)
        if 200 <= amount <= 10000:
            bot.send_message(
                message.chat.id,
                "💰 **Apna Paws Address bhejein:**\n(Ex: `/pawsaddress XYZ123`)"
            )
            bot.register_next_step_handler(
                message, lambda msg: confirm_withdraw(msg, amount))
        else:
            bot.send_message(
                message.chat.id,
                "❌ **Kripya 200-10,000 Paws ke beech amount dalein!**")
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ **Galat format! Kripya sahi amount dalein.**")


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
    update = telebot.types.Update.de_json(request.get_json())
    bot.process_new_updates([update])
    return "OK", 200


def run_flask():
    app.run(host="0.0.0.0", port=8080)


# ✅ Webhook Setup (Fix URL)
WEBHOOK_URL = f"https://f09b40d8-9592-4c05-abc6-6dceb097dd4d-00-1756mgmiwos6y.pike.replit.dev/{TOKEN}"
requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook",
              json={"url": WEBHOOK_URL})

print("🤖 Bot is running with Webhook!")

# ✅ Run Flask Server in a Separate Thread
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
