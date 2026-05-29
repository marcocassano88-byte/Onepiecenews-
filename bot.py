import os
import time
import hashlib
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🔥 prende immagine dal link dell'articolo
def get_image_from_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        # prova og:image (metodo principale)
        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]

        # fallback (alcuni siti usano twitter:image)
        img = soup.find("meta", property="twitter:image")
        if img and img.get("content"):
            return img["content"]

    except:
        pass

    return None

while True:
    feed = feedparser.parse(RSS_FEED)

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link

        uid = make_id(title)

        if uid in posted:
            continue

        posted.add(uid)

        image = get_image_from_page(link)

        # fallback sicuro se non trova immagine
        if not image:
            image = "https://i.imgur.com/8Km9tLL.jpg"

        message = f"🔥 {title}\n\n👉 Fonte: {link}"

        try:
            bot.send_photo(
                chat_id=CHAT_ID,
                photo=image,
                caption=message
            )

            print("POST:", title)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("⏳ Attendo nuovi articoli...")
    time.sleep(300)
