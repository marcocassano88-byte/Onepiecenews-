import telegram
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=BOT_TOKEN)

posts = [
    "🔥 One Piece: nuove teorie su Imu e il Secolo Vuoto!\n\n#onepiece #anime",
    "🏴‍☠️ Eiichiro Oda anticipa eventi clamorosi del finale di One Piece.\n\n#luffy #onepiece",
    "⚔️ Zoro continua a essere uno dei personaggi più amati della serie.\n\n#zoro #onepiece",
    "🔥 Gear 5 continua a dominare il fandom anime mondiale.\n\n#gear5 #luffy",
    "👑 Shanks potrebbe conoscere il vero tesoro One Piece.\n\n#shanks #onepiece",
]

for post in posts:

    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text=post
        )

        print("Post inviato")

        time.sleep(20)

    except Exception as e:
        print(e)
