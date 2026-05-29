import os
import asyncio
import hashlib
import feedparser
from telegram import Bot

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Nuova galleria con link istituzionali e stabili (Niente più blocchi IP)
GALLERY = {
    "netflix": [
        "https://upload.wikimedia.org/wikipedia/commons/f/f4/Netflix_-_logo.svg" # Logo Netflix ufficiale
    ],
    "live_action": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/One_Piece_Wall_Sign_at_the_Mugiwara_Store_in_Shibuya.jpg/1200px-One_Piece_Wall_Sign_at_the_Mugiwara_Store_in_Shibuya.jpg"
    ],
    "milano": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Milano_-_Piazza_Duomo.jpg/1200px-Milano_-_Piazza_Duomo.jpg" # Duomo di Milano
    ],
    "luffy": [
        "https://upload.wikimedia.org/wikipedia/it/b/b7/Monkey_D._Rufy.png" # Rufy Wikipedia Italia
    ],
    "zoro": [
        "https://upload.wikimedia.org/wikipedia/it/2/23/Roronoa_Zoro.png" # Zoro Wikipedia Italia
    ],
    "sanji": [
        "https://upload.wikimedia.org/wikipedia/it/e/e0/Sanji.png" # Sanji Wikipedia Italia
    ],
    "nami_robin": [
        "https://upload.wikimedia.org/wikipedia/it/7/77/Nami_%28One_Piece%29.png" # Nami Wikipedia
    ],
    "imu_governo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Jolly_Roger_of_the_World_Government_%28One_Piece%29.svg/1200px-Jolly_Roger_of_the_World_Government_%28One_Piece%29.svg.png" # Bandiera Governo Mondiale
    ],
    "generiche": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Jolly_Roger_Straw_Hat_Pirates.svg/1200px-Jolly_Roger_Straw_Hat_Pirates.svg.png" # Jolly Roger Ciurma
    ]
}

KEYWORDS_MAP = {
    "netflix": ["netflix", "remake", "wit studio", "the one piece", "wit", "serie tv", "streaming", "episodi", "puntate"],
    "live_action": ["live action", "live-action", "iñaki godoy", "inaki godoy", "mackenyu", "taz skylar", "emily rudd", "jacob romero", "matt owens", "stagione 2", "season 2", "attori", "cast", "steven maeda", "alvida", "buggy", "arlong", "garp", "koby", "helmeppo", "marina", "smoker", "loguetown", "crocus", "laboon", "vivi", "chopper", "robin", "baroque works", "mr 3", "miss wednesday"],
    "milano": ["milano", "pop-up", "store", "duomo", "mondadori", "piazza duomo", "evento", "italia", "caccia al tesoro", "negozio"],
    "luffy": ["luffy", "rufypirata", "rufy", "rubber", "gear 5", "gear fifth", "nika", "joy boy", "joyboy", "frutto del diavolo", "gom gom", "gomu gomu", "re dei pirati", "haki conquistatore", "ciurma"],
    "zoro": ["zoro", "roronoa", "spadaccino", "tre spade", "enma", "wado ichimonji", "shusui", "sandai kitetsu", "mihawk", "asura"],
    "sanji": ["sanji", "vinsmoke", "gamba nera", "cuoco", "all blue", "diable jambe", "ifrit jambe", "germa 66", "baratie", "zekeff"],
    "nami_robin": ["nami", "gatta ladra", "navigatrice", "clima tact", "nico robin", "bambina demoniaca", "archeologa", "ohara", "poneglyph", "poneglif", "rio poneglyph", "hana hana"],
    "imu_governo": ["imu", "im", "gorosei", "cinque astri", "astri di saggezza", "governo mondiale", "trono vuoto", "mary geoise", "marijoa", "draghi celesti", "nobili mondiali", "saturn", "mars", "warcury", "v. nasujuro", "ju peter", "cipher pol", "cp0"]
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def select_best_image(title):
    t = title.lower()
    for category, keywords in KEYWORDS_MAP.items():
        for keyword in keywords:
            if keyword in t:
                return GALLERY[category][0]
    return GALLERY["generiche"][0]

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t or "rufy" in t: tags.append("#luffy")
    if "netflix" in t: tags.append("#netflix")
    if "milano" in t: tags.append("#onepiecemilano")
    if "zoro" in t: tags.append("#zoro")
    if "sanji" in t: tags.append("#sanji")
    return " ".join(tags)

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    feed = feedparser.parse(RSS_FEED)
    new_posts_counter = 0

    print(f"Trovati {len(feed.entries)} articoli nel feed RSS.")

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        uid = make_id(title)

        # === FORZATURA RESET (Mantenuta per sbloccare l'invio immediato delle 10 notizie) ===
        # if uid in posted:
        #     print(f"Saltato: {title}")
        #     continue

        print(f"Elaborazione: {title}")
        img_url = select_best_image(title)
        
        try:
            # Mandiamo direttamente l'URL a Telegram, bypassando i controlli IP anti-bot
            message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"
            
            await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message)
            print(f"Inviato con successo tramite URL nativo!")
            
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
            
        except Exception as e:
            print(f"Errore Telegram: {e}")

    print(f"Fine. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
