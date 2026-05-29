import os
import time
import hashlib
from telegram import Bot
import feedparser
from deep_translator import GoogleTranslator

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

RSS_FEED = "https://www.animenewsnetwork.com/all/rss.xml"

posted = set()

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='it').translate(text)
    except:
        return text

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

        title_it = translate(title)

        message = f"🔥 {title_it}\n\n👉 Fonte: {link}"

        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print("POST:", title_it)

        except Exception as e:
            print("Errore:", e)

        time.sleep(20)

    print("Attendo nuovo ciclo...")
    time.sleep(300)
