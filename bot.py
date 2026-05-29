import os
import time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

posts = [
    "🔥 One Piece: nuove teorie su Imu e il Secolo Vuoto",
    "🏴‍☠️ Luffy continua la sua corsa verso il One Piece",
    "⚔️ Zoro e il suo ruolo da vice-capitano non ufficiale",
    "👑 Shanks e i segreti del Nuovo Mondo",
    "🔥 Gear 5 domina il mondo degli anime",
    "📜 Il mistero del Secolo Vuoto si infittisce",
    "🌊 La Grand Line nasconde ancora segreti incredibili",
    "💀 Blackbeard punta al dominio totale",
    "🧭 Nami e la mappa del mondo",
    "🏝️ Wano ha cambiato tutto nella storia",
    "🔥 Il Governo Mondiale trema",
    "⚔️ Mihawk resta il miglior spadaccino",
    "👒 Luffy diventa sempre più vicino al sogno",
    "💥 Il Gear 5 ha cambiato le regole del combattimento",
    "🏴‍☠️ La ciurma di Cappello di Paglia cresce in potenza"
]

for post in posts:
    try:
        bot.send_message(chat_id=CHAT_ID, text=post)
        print("OK:", post)

        time.sleep(40)  # anti flood serio

    except Exception as e:
        print("Errore:", e)
        time.sleep(20)
