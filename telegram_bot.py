import os
import re
import telebot
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Perfectly!"

def run():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ഒറിജിനൽ ടോക്കൺ ഇവിടെ സെറ്റ് ചെയ്തിട്ടുണ്ട് ---
BOT_TOKEN = "8829939412:AAFCSWd3CXPk8LJ0cm_IJujH7_WRAJ5dzG4"
bot = telebot.TeleBot(BOT_TOKEN)

# കീവേർഡുകൾ (Keywords)
GRAPHIC_KEYWORDS = re.compile(r"graphic|display|light|screen|ചിത്രം|ഡിസ്പ്ലേ", re.IGNORECASE)
NETWORK_KEYWORDS = re.compile(r"network|no service|signal|നെറ്റ്‌വർക്ക്|സിഗ്നൽ", re.IGNORECASE)
DC_KEYWORDS = re.compile(r"dc reading|dc machine|റീഡിങ്|ഡിസി", re.IGNORECASE)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **മൊബൈൽ ഹാർഡ്‌വെയർ റിപ്പയർ ബോട്ടിലേക്ക് സ്വാഗതം!**\n\n"
        "നിങ്ങളുടെ സംശയങ്ങൾ താഴെ പറയുന്ന രീതിയിൽ ചോദിക്കാം:\n"
        "🔹 `Graphic issue` അല്ലെങ്കിൽ `Display`\n"
        "🔹 `No service` അല്ലെങ്കിൽ `Network`\n"
        "🔹 `DC reading` അല്ലെങ്കിൽ `DC machine`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    
    if GRAPHIC_KEYWORDS.search(text):
        response = (
            "📱 **Graphic / Display Section Diagnostic Steps:**\n\n"
            "1. **Visual Inspection:** എൽസിഡി കണക്ടറും എഫ്പിസി (FPC) കേബിളും കേടുപാടുകൾ ഉണ്ടോ എന്ന് നോക്കുക.\n"
            "2. **Voltage Check:** എൽസിഡി കണക്ടറിൽ `+5V` (VSP) കൂടാതെ `-5V` (VSN) വോൾട്ടേജുകൾ വരുന്നുണ്ടോ എന്ന് ചെക്ക് ചെയ്യുക.\n"
            "3. **MIPI Lines:** പ്രൊസസ്സറിൽ നിന്ന് വരുന്ന MIPI ലൈനുകളുടെ ഡയോഡ് വാല്യൂസ് (Diode Value) മൾട്ടിമീറ്റർ വെച്ച് അളക്കുക."
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    elif NETWORK_KEYWORDS.search(text):
        response = (
            "📶 **4G / 5G Network Section Diagnostic Steps:**\n\n"
            "1. **WTR / Transceiver IC:** നോ സർവീസ് (No Service) പ്രശ്നങ്ങൾക്ക് ആദ്യം WTR IC-യുടെ വോൾട്ടേജുകൾ (1.0V, 1.8V) ചെക്ക് ചെയ്യുക.\n"
            "2. **PA (Power Amplifier):** 4G/2G പിഎ (PA) സെക്ഷനിലേക്ക് VPH_PWR വോൾട്ടേജ് കൃത്യമായി കിട്ടുന്നുണ്ടോ എന്ന് നോക്കുക.\n"
            "3. **Antenna Switch:** ആന്റിന സ്വിച്ചും ക്രിസ്റ്റൽ ഓസിലേറ്ററും (XO) കേടാണോ എന്ന് ഉറപ്പുവരുത്തുക."
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    elif DC_KEYWORDS.search(text):
        response = (
            "⚡ **DC Power Supply Machine Readings & Faults:**\n\n"
            "🔹 **0.00A (No Auto Amp):** പവർ ബട്ടൺ ഞെക്കുമ്പോൾ റീഡിങ് ഇല്ലെങ്കിൽ പവർ ബട്ടൺ ലൈൻ, പവർ ഐസി (PMIC) എന്നിവ ചെക്ക് ചെയ്യുക.\n"
            "🔹 **0.01A - 0.05A Stuck:** ഇത് സാധാരണയായി സിപിയു (CPU) അല്ലെങ്കിൽ റാം (RAM) കമ്മ്യൂണിക്കേഷൻ ഫെയിലിയർ (Dead Boot) ആയിരിക്കാം.\n"
            "🔹 **Auto Amperage (Shorting):** പവർ ബട്ടൺ അമർത്തുന്നതിന് മുൻപ് റീഡിങ് കാണിച്ചാൽ വിപിഎച്ച് (VPH) അല്ലെങ്കിൽ വിബാറ്റ് (VBAT) ലൈനിൽ ഷോർട്ട് ഉണ്ട്."
        )
        bot.reply_to(message, response, parse_mode="Markdown")
        
    else:
        bot.reply_to(message, "ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. `Graphic`, `Network`, അല്ലെങ്കിൽ `DC reading` എന്ന് ടൈപ്പ് ചെയ്ത് നോക്കൂ.")

if __name__ == "__main__":
    keep_alive()
    print("Bot is ready to assist students...")
    bot.infinity_polling()
