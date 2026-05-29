import os
import time
import hashlib
import feedparser
from telegram import Bot
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

        # 🔥 immagine automatica dal feed (OG IMAGE se esiste)
        image = None

        if "media_content" in entry:
            try:
                image = entry.media_content[0]["url"]
            except:
                pass

        if not image:
            image = "https://i.imgur.com/8Km9tLL.jpg"  # fallback

        caption = f"🔥 {title_it}\n\n👉 Fonte: {link}"

        try:
            bot.send_photo(
                chat_id=CHAT_ID,
                photo=image,
                caption=caption
            )

            print("POST:", title_it)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("Attendo nuovi articoli...")
    time.sleep(300)
