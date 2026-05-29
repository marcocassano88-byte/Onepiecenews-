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

# 🔥 immagine dal link
def get_image_from_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]

        img = soup.find("meta", property="twitter:image")
        if img and img.get("content"):
            return img["content"]

    except:
        pass

    return None

# 🔥 generatore hashtag automatico
def generate_hashtags(title):
    title = title.lower()

    hashtags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in title:
        hashtags.append("#luffy")
    if "zoro" in title:
        hashtags.append("#zoro")
    if "shanks" in title:
        hashtags.append("#shanks")
    if "gear 5" in title or "gear5" in title:
        hashtags.append("#gear5")
    if "imu" in title:
        hashtags.append("#imu")
    if "wano" in title:
        hashtags.append("#wano")

    return " ".join(hashtags)

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

        if not image:
            image = "https://i.imgur.com/8Km9tLL.jpg"

        hashtags = generate_hashtags(title)

        message = f"""🔥 {title}

👉 Fonte: {link}

{hashtags}"""

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
