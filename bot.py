import os
import time
import hashlib
import random
import feedparser
import requests
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🖼️ IMMAGINI STABILI (URL DIRETTI TESTATI)
images = {
    "luffy": [
        "https://static.wikia.nocookie.net/onepiece/images/5/56/Luffy_Gear_5.png",
        "https://static.wikia.nocookie.net/onepiece/images/8/80/Luffy_Anime.png"
    ],
    "zoro": [
        "https://static.wikia.nocookie.net/onepiece/images/6/65/Zoro_Post_Timeskip.png"
    ],
    "shanks": [
        "https://static.wikia.nocookie.net/onepiece/images/5/58/Shanks.png"
    ],
    "nami": [
        "https://static.wikia.nocookie.net/onepiece/images/2/2f/Nami_Anime.png"
    ],
    "default": [
        "https://static.wikia.nocookie.net/onepiece/images/2/2a/One_Piece_Logo.png"
    ]
}

# 🔥 trova immagine
def get_image(title):
    t = title.lower()

    for key in images:
        if key in t:
            return random.choice(images[key])

    return random.choice(images["default"])

# 🔥 hashtag
def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "shanks" in t: tags.append("#shanks")
    if "gear 5" in t: tags.append("#gear5")

    return " ".join(tags)

# 🚀 LOOP
while True:
    feed = feedparser.parse(RSS_FEED)

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link

        uid = make_id(title)

        if uid in posted:
            continue

        posted.add(uid)

        image_url = get_image(title)

        message = f"""🔥 {title}

👉 Fonte: {link}

{hashtags(title)}"""

        try:
            # 🔥 SEMPRE send_photo (mai fallback text)
            bot.send_photo(
                chat_id=CHAT_ID,
                photo=image_url,
                caption=message
            )

            print("POST:", title)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("⏳ Attendo nuovi articoli...")
    time.sleep(300)
