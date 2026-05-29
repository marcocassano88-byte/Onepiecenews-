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

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🧠 100 PERSONAGGI → MAPPA CATEGORIE WIKIMEDIA
characters_map = {
    "luffy": "Monkey D. Luffy",
    "zoro": "Roronoa Zoro",
    "nami": "Nami (One Piece)",
    "usopp": "Usopp",
    "sanji": "Sanji",
    "chopper": "Tony Tony Chopper",
    "robin": "Nico Robin",
    "franky": "Franky",
    "brook": "Brook",
    "jimbei": "Jinbe",

    "shanks": "Shanks (One Piece)",
    "buggy": "Buggy (One Piece)",
    "mihawk": "Dracule Mihawk",
    "law": "Trafalgar Law",
    "kid": "Eustass Kid",
    "sabo": "Sabo (One Piece)",
    "ace": "Portgas D. Ace",
    "whitebeard": "Edward Newgate",
    "kaido": "Kaido",
    "big mom": "Charlotte Linlin",

    "roger": "Gol D. Roger",
    "dragon": "Monkey D. Dragon",
    "garp": "Monkey D. Garp",
    "akainu": "Sakazuki",
    "aokiji": "Kuzan",
    "kizaru": "Borsalino",
    "imu": "Imu (One Piece)",

    "doflamingo": "Donquixote Doflamingo",
    "crocodile": "Crocodile (One Piece)",
    "enel": "Enel (One Piece)",
    "lucci": "Rob Lucci",
    "kuma": "Bartholomew Kuma",
    "bonney": "Jewelry Bonney",

    "yamato": "Yamato (One Piece)",
    "momonosuke": "Momonosuke",
    "kinemon": "Kin'emon",

    "moria": "Gecko Moria",
    "hancock": "Boa Hancock",
    "ivankov": "Emporio Ivankov",

    "rocks": "Rocks D. Xebec",

    "gear 5": "Monkey D. Luffy",
    "joy boy": "Joy Boy",
    "nika": "Nika (One Piece)"
}

# 🔥 PRENDE IMMAGINI REALI DA CATEGORIA WIKIMEDIA
def get_wiki_image(category_name):
    try:
        url = "https://commons.wikimedia.org/w/api.php"

        # 1️⃣ prendi file dalla categoria
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": "Category:" + category_name,
            "cmtype": "file",
            "cmlimit": 50
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        files = data.get("query", {}).get("categorymembers", [])

        if not files:
            return None

        random_file = random.choice(files)["title"]

        # 2️⃣ ottieni URL immagine reale
        params2 = {
            "action": "query",
            "format": "json",
            "titles": random_file,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        r2 = requests.get(url, params=params2, timeout=10)
        data2 = r2.json()

        pages = data2.get("query", {}).get("pages", {})

        for p in pages.values():
            if "imageinfo" in p:
                return p["imageinfo"][0]["url"]

    except:
        pass

    return None

# 🖼️ CACHE (evita richieste continue)
def get_character_image(title):
    t = title.lower()

    for key, category in characters_map.items():
        if key in t:
            cache_path = os.path.join(CACHE_DIR, key + ".jpg")

            if os.path.exists(cache_path):
                return cache_path

            img_url = get_wiki_image(category)

            if img_url:
                try:
                    img_data = requests.get(img_url, timeout=10).content
                    with open(cache_path, "wb") as f:
                        f.write(img_data)
                    return cache_path
                except:
                    pass

    # fallback generale
    cache_path = os.path.join(CACHE_DIR, "default.jpg")

    if os.path.exists(cache_path):
        return cache_path

    img_url = get_wiki_image("One Piece")

    if img_url:
        img_data = requests.get(img_url, timeout=10).content
        with open(cache_path, "wb") as f:
            f.write(img_data)
        return cache_path

    return None

# 🔥 HASHTAG AUTOMATICI
def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "shanks" in t: tags.append("#shanks")
    if "gear 5" in t: tags.append("#gear5")
    if "imu" in t: tags.append("#imu")

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

        message = f"""🔥 {title}

👉 Fonte: {link}

{hashtags(title)}"""

        try:
            if image:
                bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=open(image, "rb"),
                    caption=message
                )
            else:
                bot.send_message(chat_id=CHAT_ID, text=message)

            print("POST:", title)

        except Exception as e:
            print("Errore:", e)

        time.sleep(25)

    print("⏳ Attendo nuovi articoli...")
    time.sleep(300)
