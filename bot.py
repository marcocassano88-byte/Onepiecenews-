import os
import time
import hashlib
import feedparser
import requests
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

CACHE_DIR = "cache"

os.makedirs(CACHE_DIR, exist_ok=True)

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🔥 100 PERSONAGGI ONE PIECE
characters_map = {
    "luffy": "Monkey D. Luffy One Piece",
    "zoro": "Roronoa Zoro One Piece",
    "nami": "Nami One Piece",
    "usopp": "Usopp One Piece",
    "sanji": "Sanji One Piece",
    "chopper": "Tony Tony Chopper One Piece",
    "robin": "Nico Robin One Piece",
    "franky": "Franky One Piece",
    "brook": "Brook One Piece",
    "jimbei": "Jinbe One Piece",

    "shanks": "Shanks One Piece",
    "buggy": "Buggy One Piece",
    "mihawk": "Dracule Mihawk One Piece",
    "law": "Trafalgar Law One Piece",
    "kid": "Eustass Kid One Piece",
    "sabo": "Sabo One Piece",
    "ace": "Portgas D Ace One Piece",
    "whitebeard": "Edward Newgate Whitebeard One Piece",
    "kaido": "Kaido One Piece",
    "big mom": "Charlotte Linlin One Piece",

    "roger": "Gol D Roger One Piece",
    "dragon": "Monkey D Dragon One Piece",
    "garp": "Monkey D Garp One Piece",
    "akainu": "Sakazuki Akainu One Piece",
    "aokiji": "Kuzan Aokiji One Piece",
    "kizaru": "Borsalino Kizaru One Piece",
    "imu": "Imu One Piece",

    "doflamingo": "Donquixote Doflamingo One Piece",
    "crocodile": "Crocodile One Piece",
    "enel": "Enel One Piece",
    "lucci": "Rob Lucci One Piece",
    "kuma": "Bartholomew Kuma One Piece",
    "bonney": "Jewelry Bonney One Piece",

    "yamato": "Yamato One Piece",
    "momonosuke": "Momonosuke One Piece",
    "kinemon": "Kinemon One Piece",

    "moria": "Gecko Moria One Piece",
    "hancock": "Boa Hancock One Piece",
    "ivankov": "Emporio Ivankov One Piece",

    "rocks": "Rocks D Xebec One Piece",

    "gear 5": "Gear 5 Luffy One Piece",
    "joy boy": "Joy Boy One Piece",
    "nika": "Nika Luffy One Piece"
}

# 🔥 scarica immagine e la salva in cache
def get_image(query, key):
    cache_path = os.path.join(CACHE_DIR, f"{key}.jpg")

    # se esiste già → usa cache
    if os.path.exists(cache_path):
        return cache_path

    try:
        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 1,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        pages = data.get("query", {}).get("pages", {})

        for p in pages.values():
            if "imageinfo" in p:
                img_url = p["imageinfo"][0]["url"]

                img_data = requests.get(img_url).content

                with open(cache_path, "wb") as f:
                    f.write(img_data)

                return cache_path

    except:
        pass

    return None

# 🔥 trova immagine personaggio
def get_character_image(title):
    title = title.lower()

    for key, query in characters_map.items():
        if key in title:
            return get_image(query, key)

    # fallback One Piece generico
    return get_image("One Piece anime", "default")

# 🔥 hashtag
def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "shanks" in t: tags.append("#shanks")
    if "gear 5" in t: tags.append("#gear5")
    if "imu" in t: tags.append("#imu")

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

        image = get_character_image(title)

        message = f"""🔥 {title}

👉 Fonte: {link}

{hashtags(title)}"""

        try:
            if image:
                bot.send_photo(chat_id=CHAT_ID, photo=open(image, "rb"), caption=message)
            else:
                bot.send_message(chat_id=CHAT_ID, text=message)

            print("POST:", title)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("⏳ Attendo nuovi articoli...")
    time.sleep(300)
