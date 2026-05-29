import os
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("TOKEN DEBUG:", BOT_TOKEN)  # SOLO TEST TEMPORANEO

bot = Bot(token=BOT_TOKEN)

bot.send_message(chat_id=CHAT_ID, text="TEST BOT OK ✅")
