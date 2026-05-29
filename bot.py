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

# 🔥 IMMAGINI SOLO ONE PIECE (WIKIMEDIA = STABILE)
def get_image(query):
    try:
        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query + " one piece",
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        pages = data.get("query", {}).get("pages", {})

        images = []

        for page in pages.values():
            if "imageinfo" in page:
                images.append(page["imageinfo"][0]["url"])

        if images:
            return random.choice(images)

    except:
        pass

    return None

# 🔥 PERSONAGGI
def get_character_image(title):
    title = title.lower()

    characters = {
        "luffy": "luffy",
        "zoro": "zoro",
        "nami": "nami",
        "sanji": "sanji",
        "usopp": "usopp",
        "chopper": "chopper",
        "robin": "robin",
        "franky": "franky",
        "brook": "brook",
        "jimbei": "jinbe",

        "shanks": "shanks",
        "buggy": "buggy",
        "kaido": "kaido",
        "big mom": "big mom",
        "whitebeard": "whitebeard",
        "roger": "roger",

        "law": "trafalgar law",
        "kid": "eustass kid",
        "sabo": "sabo",
        "yamato": "yamato",

        "akainu": "akainu",
        "aokiji": "aokiji",
        "kizaru": "kizaru",
        "garp": "garp",
        "sengoku": "sengoku",
        "imu": "imu",

        "mihawk": "mihawk",
        "doflamingo": "doflamingo",
        "crocodile": "crocodile",

        "gear 5": "gear 5 luffy",
        "joy boy": "joy boy"
    }

    for key, query in characters.items():
        if key in title:
            return get_image(query)

    # fallback sicuro
    return get_image("one piece anime")

# 🔥 HASHTAG
def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime"]

    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "shanks" in t: tags.append("#shanks")
    if "gear 5" in t: tags.append("#gear5")
    if "imu" in t: tags.append("#imu")

    return " ".join(tags)

while True:
    feed = feedparser.parse(RSS_FEED)

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link

        uid = make_id(title)

        if uid in posted:
            continue

        posted.add(uid)

        image = get_character_image(title)

        if not image:
            image = "https://i.imgur.com/8Km9tLL.jpg"

        message = f"""🔥 {title}

👉 Fonte: {link}

{hashtags(title)}"""

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

    time.sleep(300)
