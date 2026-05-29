import os
import time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

posts = [
    ("🔥 One Piece: mistero del Secolo Vuoto", "https://onepiece.fandom.com/wiki/Void_Century"),
    ("🏴‍☠️ Luffy verso il One Piece", "https://onepiece.fandom.com/wiki/Monkey_D._Luffy"),
    ("⚔️ Zoro spadaccino leggendario", "https://onepiece.fandom.com/wiki/Roronoa_Zoro"),
    ("👑 Shanks e il Nuovo Mondo", "https://onepiece.fandom.com/wiki/Shanks"),
    ("🔥 Gear 5 spiegato", "https://onepiece.fandom.com/wiki/Gomu_Gomu_no_Mi/Gear_5")
]

for title, link in posts * 10:
    try:
        text = f"{title}\n👉 {link}"

        bot.send_message(chat_id=CHAT_ID, text=text)

        print("OK:", title)

        time.sleep(40)

    except Exception as e:
        print("Errore:", e)
        time.sleep(20)
