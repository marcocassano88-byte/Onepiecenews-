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

# 🔥 RSS RESTA IDENTICO (come volevi)
RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

posted = set()

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🔥 ricerca immagini online
def search_image(query):
    try:
        url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=10)

        import re
        imgs = re.findall(r'"image":"(.*?)"', r.text)

        if imgs:
            return random.choice(imgs)
    except:
        pass

    return None

# 🔥 immagini per personaggio + fallback intelligente
def get_character_image(title):
    title = title.lower()

    characters = {
        "luffy": "luffy one piece",
        "zoro": "zoro one piece",
        "nami": "nami one piece",
        "usopp": "usopp one piece",
        "sanji": "sanji one piece",
        "chopper": "chopper one piece",
        "robin": "nico robin one piece",
        "franky": "franky one piece",
        "brook": "brook one piece",
        "jimbei": "jinbe one piece",

        "law": "trafalgar law one piece",
        "kid": "eustass kid one piece",
        "sabo": "sabo one piece",
        "yamato": "yamato one piece",

        "shanks": "shanks one piece",
        "buggy": "buggy one piece",
        "blackbeard": "blackbeard one piece",
        "teach": "blackbeard one piece",
        "whitebeard": "whitebeard one piece",
        "kaido": "kaido one piece",
        "big mom": "big mom one piece",
        "roger": "gol d roger one piece",

        "akainu": "akainu one piece",
        "aokiji": "aokiji one piece",
        "kizaru": "kizaru one piece",
        "garp": "garp one piece",
        "sengoku": "sengoku one piece",
        "imu": "imu one piece",

        "dragon": "dragon one piece",
        "mihawk": "mihawk one piece",
        "crocodile": "crocodile one piece",
        "doflamingo": "doflamingo one piece",
        "hancock": "boa hancock one piece",

        "gear 5": "gear 5 luffy one piece",
        "joy boy": "joy boy one piece",
        "nika": "nika luffy one piece",

        # LIVE ACTION NETFLIX
        "live action luffy": "one piece netflix luffy",
        "live action zoro": "one piece netflix zoro",
        "live action nami": "one piece netflix nami",
        "live action sanji": "one piece netflix sanji",
        "live action usopp": "one piece netflix usopp",
        "live action garp": "one piece netflix garp",
        "live action buggy": "one piece netflix buggy",
        "live action mihawk": "one piece netflix mihawk"
    }

    for key, query in characters.items():
        if key in title:
            return search_image(query)

    # 🎲 fallback random controllato
    fallback = [
        "one piece luffy",
        "one piece zoro",
        "one piece shanks",
        "one piece gear 5",
        "one piece anime",
        "one piece manga"
    ]

    return search_image(random.choice(fallback))

# 🔥 HASHTAG AUTOMATICI
def generate_hashtags(title):
    title = title.lower()

    tags = ["#onepiece", "#anime", "#manga"]

    if "luffy" in title:
        tags.append("#luffy")
    if "zoro" in title:
        tags.append("#zoro")
    if "shanks" in title:
        tags.append("#shanks")
    if "gear 5" in title:
        tags.append("#gear5")
    if "imu" in title:
        tags.append("#imu")
    if "wano" in title:
        tags.append("#wano")

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
