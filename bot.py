from telegram import Bot

BOT_TOKEN = "INSERISCI_TOKEN"
CHAT_ID = "@nomecanale"

bot = Bot(token=BOT_TOKEN)

try:
    bot.send_message(chat_id=CHAT_ID, text="TEST BOT OK ✅")
    print("FUNZIONA")
except Exception as e:
    print("ERRORE:", e)
