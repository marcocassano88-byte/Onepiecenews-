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

# 🔥 RSS (NON CAMBIATO)
RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🖼️ IMMAGINI DA WIKIMEDIA (STABILI + HD)
def get_wiki_images(query):
    try:
        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 20,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        pages = data.get("query", {}).get("pages", {})

        images = []

        for p in pages.values():
            if "imageinfo" in p:
                images.append(p["imageinfo"][0]["url"])

        if images:
            return random.choice(images)

    except:
        pass

    return None

# 🔥 100+ PERSONAGGI ONE PIECE + LIVE ACTION
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
    "ace": "Portgas D. Ace One Piece",
    "whitebeard": "Edward Newgate Whitebeard One Piece",
    "kaido": "Kaido One Piece",
    "big mom": "Charlotte Linlin Big Mom One Piece",

    "roger": "Gol D. Roger One Piece",
    "dragon": "Monkey D. Dragon One Piece",
    "garp": "Monkey D. Garp One Piece",
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

    "gecko moria": "Gecko Moria One Piece",
    "hancock": "Boa Hancock One Piece",
    "ivankov": "Emporio Ivankov One Piece",

    "rocks": "Rocks D Xebec One Piece",

    "luffy gear 5": "Gear 5 Luffy One Piece",
    "joy boy": "Joy Boy One Piece",
    "nika": "Nika Luffy One Piece",

    # 🎬 LIVE ACTION NETFLIX
    "live action luffy": "One Piece Netflix Luffy",
    "live action zoro": "One Piece Netflix Zoro",
    "live action nami": "One Piece Netflix Nami",
    "live action sanji": "One Piece Netflix Sanji",
    "live action usopp": "One Piece Netflix Usopp",
    "live action garp": "One Piece Netflix Garp",
    "live action buggy": "One Piece Netflix Buggy",
    "live action mihawk": "One Piece Netflix Mihawk"
}

# 🖼️ trova immagine personaggio
def get_character_image(title):
    title = title.lower()

    for key, query in characters_map.items():
        if key in title:
            return get_wiki_images(query)

    return get_wiki_images("One Piece anime")

# 🔥 HASHTAG AUTOMATICI
def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in t:
        tags.append("#luffy")
    if "zoro" in t:
        tags.append("#zoro")
    if "shanks" in t:
        tags.append("#shanks")
    if "gear 5" in t:
        tags.append("#gear5")
    if "imu" in t:
        tags.append("#imu")

    return " ".join(tags)

# 🚀 LOOP PRINCIPALE
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

    print("⏳ Attendo nuovi articoli...")
    time.sleep(300)
