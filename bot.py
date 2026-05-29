import os
import time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

posts = [
    {
        "title": "🔥 One Piece: il mistero del Secolo Vuoto",
        "image": "https://i.imgur.com/8Km9tLL.jpg",
        "link": "https://onepiece.fandom.com/wiki/Void_Century"
    },
    {
        "title": "🏴‍☠️ Luffy sempre più vicino al One Piece",
        "image": "https://i.imgur.com/1X4h2xB.jpg",
        "link": "https://onepiece.fandom.com/wiki/Monkey_D._Luffy"
    },
    {
        "title": "⚔️ Zoro, il miglior spadaccino della ciurma",
        "image": "https://i.imgur.com/3YQjQ9L.jpg",
        "link": "https://onepiece.fandom.com/wiki/Roronoa_Zoro"
    },
    {
        "title": "👑 Shanks e i segreti del Nuovo Mondo",
        "image": "https://i.imgur.com/5rVZ7kF.jpg",
        "link": "https://onepiece.fandom.com/wiki/Shanks"
    },
    {
        "title": "🔥 Gear 5: la forma più potente di Luffy",
        "image": "https://i.imgur.com/9zQZ9aA.jpg",
        "link": "https://onepiece.fandom.com/wiki/Gomu_Gomu_no_Mi/Gear_5"
    }
]

# 🔥 RIEMPIMENTO 50 POST
for post in posts * 10:
    try:
        caption = f"{post['title']}\n👉 Approfondisci: {post['link']}"

        bot.send_photo(
            chat_id=CHAT_ID,
            photo=post["image"],
            caption=caption
        )

        print("OK:", post["title"])
        time.sleep(45)  # anti flood

    except Exception as e:
        print("Errore:", e)
        time.sleep(20)
