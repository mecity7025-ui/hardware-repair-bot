import os
import telebot
from flask import Flask
from threading import Thread

# Web Server for Render 24/7
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Telegram Bot Token ---
BOT_TOKEN = "8995026422:AAHjalJO7cf85skxE1sYh14N7LlmjUQ4ocQ" 
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "മൊബൈൽ ഹാർഡ്‌വെയർ റിപ്പയർ ബോട്ടിലേക്ക് സ്വാഗതം! നിങ്ങൾക്ക് ഏത് സെക്ഷനെക്കുറിച്ചാണ് അറിയേണ്ടത്?")

# Bot Run cheyyunnu
if __name__ == "__main__":
    keep_alive() # Server run cheyyikkaan
    print("Bot is starting...")
    bot.infinity_polling()
