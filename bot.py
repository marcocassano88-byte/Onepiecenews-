import os
import time
import hashlib
import feedparser
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

while True:
    feed = feedparser.parse(RSS_FEED)

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link

        uid = make_id(title)

        if uid in posted:
            continue

        posted.add(uid)

        message = f"🔥 {title}\n\n👉 Fonte: {link}"

        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print("POST:", title)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("Attendo nuovi articoli...")
    time.sleep(300)
