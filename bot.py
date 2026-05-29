import telegram
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=BOT_TOKEN)

bot.send_message(
    chat_id=CHAT_ID,
    text="✅ TEST RIUSCITO - Il bot Telegram funziona correttamente!"
)

print("Messaggio inviato")
