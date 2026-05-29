import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
import random

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Galleria Premium con oltre 100 parole chiave mappate
GALLERY = {
    "netflix": [
        "https://i.imgur.com/8Xb3GZM.jpeg",  # Poster Remake Wit Studio
        "https://i.imgur.com/M6XwX8F.jpeg"   # Logo Netflix Anime
    ],
    "live_action": [
        "https://i.imgur.com/eb8f6d13.jpeg", # Cast Live Action Season 1/2
        "https://i.imgur.com/5fe0e904.jpeg"  # Going Merry Netflix version
    ],
    "milano": [
        "https://i.imgur.com/uKFb71w.jpeg"   # Pop up store / Milano evento
    ],
    "luffy": [
        "https://i.imgur.com/b7Z7GHI.jpeg",  # Luffy Gear 5 HD
        "https://i.imgur.com/rF8YmWX.jpeg"   # Luffy classico
    ],
    "zoro": [
        "https://i.imgur.com/6W6kE6X.jpeg",  # Zoro combattimento
        "https://i.imgur.com/vHbcw7X.jpeg"   # Zoro stile Wano
    ],
    "sanji": [
        "https://i.imgur.com/2X8P3mG.jpeg",  # Sanji Ifrit Jambe
        "https://i.imgur.com/Qk9bYwM.jpeg"   # Sanji fumo
    ],
    "nami_robin": [
        "https://i.imgur.com/pZ6X8Kz.jpeg"   # Ragazze della ciurma / Archeologia e mappe
    ],
    "imu_governo": [
        "https://i.imgur.com/tY7wK8p.jpeg",  # Imu sul Trono Vuoto / Gorosei
        "https://i.imgur.com/bM9Wz4m.jpeg"   # Simbolo Governo Mondiale
    ],
    "generiche": [
        "https://i.imgur.com/W1Xz68m.jpeg",  # Ciurma intera sulla Thousand Sunny
        "https://i.imgur.com/fM9Ym9B.jpeg",  # Wano Style Poster
        "https://i.imgur.com/y8XmQwL.jpeg"   # Logo One Piece Moderno
    ]
}

# Oltre 100 parole chiave categorizzate per intercettare qualsiasi notizia
KEYWORDS_MAP = {
    "netflix": [
        "netflix", "remake", "wit studio", "the one piece", "wit", "serie tv", "streaming", "episodi", "puntate"
    ],
    "live_action": [
        "live action", "live-action", "iñaki godoy", "inaki godoy", "mackenyu", "taz skylar", "emily rudd", 
        "jacob romero", "matt owens", "stagione 2", "season 2", "attori", "cast", "steven maeda", "alvida", 
        "buggy", "arlong", "garp", "koby", "helmeppo", "marina", "smoker", "loguetown", "crocus", "laboon", 
        "vivi", "chopper", "robin", "baroque works", "mr 3", "miss wednesday", "w组织"
    ],
    "milano": [
        "milano", "pop-up", "store", "duomo", "mondadori", "piazza duomo", "evento", "italia", "caccia al tesoro", "negozio"
    ],
    "luffy": [
        "luffy", "rufypirata", "rufy", "rubber", "gear 5", "gear fifth", "nika", "joy boy", "joyboy", 
        "frutto del diavolo", "gom gom", "gomu gomu", "re dei pirati", "haki conquistatore", "ciurma"
    ],
    "zoro": [
        "zoro", "roronoa", "spadaccino", "tre spade", "enma", "wado ichimonji", "shusui", "sandai kitetsu", "mihawk", "asura"
    ],
    "sanji": [
        "sanji", "vinsmoke", "gamba nera", "cuoco", "all blue", "diable jambe", "ifrit jambe", "germa 66", "baratie", "zekeff"
    ],
    "nami_robin": [
        "nami", "gatta ladra", "navigatrice", "clima tact", "nico robin", "bambina demoniaca", "archeologa", 
        "ohara", "poneglyph", "poneglif", "rio poneglyph", "hana hana"
    ],
    "imu_governo": [
        "imu", "im", "gorosei", "cinque astri", "astri di saggezza", "governo mondiale", "trono vuoto", "mary geoise", 
        "marijoa", "draghi celesti", "nobili mondiali", "saturn", "mars", "warcury", "v. nasujuro", "ju peter", "cipher pol", "cp0"
    ]
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def select_best_image(title):
    """Scansiona il titolo cercando una corrispondenza tra le oltre 100 parole chiave."""
    t = title.lower()
    
    # Controlla ogni categoria definita nelle parole chiave
    for category, keywords in KEYWORDS_MAP.items():
        for keyword in keywords:
            if keyword in t:
                print(f"Parola chiave trovata: '{keyword}' -> Categoria: {category}")
                return random.choice(GALLERY[category])
                
    # Fallback su immagini generiche mozzafiato
    return random.choice(GALLERY["generiche"])

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t or "rufy" in t: tags.append("#luffy")
    if "netflix" in t: tags.append("#netflix")
    if "live" in t: tags.append("#onepieceliveaction")
    if "milano" in t: tags.append("#onepiecemilano")
    if "zoro" in t: tags.append("#zoro")
    if "sanji" in t: tags.append("#sanji")
    return " ".join(tags)

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti nelle variabili d'ambiente.")
        return

    bot = Bot(token=BOT_TOKEN)
    feed = feedparser.parse(RSS_FEED)
    new_posts_counter = 0

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        uid = make_id(title)

        if uid in posted:
            continue

        print(f"\nAnalisi notizia: {title}")
        
        # Selezione intelligente dell'immagine tramite il super dizionario
        img_url = select_best_image(title)
        
        try:
            img_res = requests.get(img_url, timeout=10)
            if img_res.status_code == 200:
                image_stream = io.BytesIO(img_res.content)
                image_stream.name = "one_piece_news.jpg"
                
                message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"
                
                await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message)
                print(f"Post inviato correttamente!")
                
                posted.add(uid)
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                    
                new_posts_counter += 1
                await asyncio.sleep(5)
            else:
                print(f"Errore download immagine galleria: {img_res.status_code}")
        except Exception as e:
            print(f"Errore invio Telegram: {e}")

    print(f"\nTask terminato. Post pubblicati in questa sessione: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
