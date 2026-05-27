import telebot

TOKEN = "8829939412:AAFCSWd3CXPk8LJ0cm_IJujH7_WRAJ5dzG4"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "മൊബൈൽ ഹാർഡ്‌വെയർ റിപ്പയർ ബോട്ടിലേക്ക് സ്വാഗതം! നിങ്ങൾക്ക് എന്ത് സഹായമാണ് വേണ്ടത്?")

bot.polling()
