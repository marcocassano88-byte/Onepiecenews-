import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Galleria con link STATICI reali - Niente più Larry David o blocchi
GALLERY = {
    "netflix": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Logo_of_the_Wit_Studio.svg/1200px-Logo_of_the_Wit_Studio.svg.png", # Wit Studio Remake
    "live_action": "https://i.postimg.cc/0jXm0L16/one-piece-live-action.jpg", # Poster Live Action ufficiale
    "milano": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Milano_Mondadori_Duomo.jpg/1200px-Milano_Mondadori_Duomo.jpg", # Mondadori Duomo
    "luffy": "https://i.postimg.cc/Vv3XwX8M/luffy-gear5.jpg", # Luffy Gear 5
    "zoro": "https://i.postimg.cc/9F7bM6z7/zoro.jpg", # Zoro
    "sanji": "https://i.postimg.cc/4N5Vdfm8/sanji.jpg", # Sanji
    "generiche": "https://i.postimg.cc/bN1mK7Yx/one-piece-crew.jpg" # Ciurma completa
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def select_best_image(title):
    t = title.lower()
    if "netflix" in t or "remake" in t or "wit" in t:
        return GALLERY["netflix"]
    elif "live" in t or "action" in t or "attori" in t:
        return GALLERY["live_action"]
    elif "milano" in t or "store" in t or "pop-up" in t:
        return GALLERY["milano"]
    elif "zoro" in t:
        return GALLERY["zoro"]
    elif "sanji" in t:
        return GALLERY["sanji"]
    elif "luffy" in t or "rufy" in t or "gear" in t:
        return GALLERY["luffy"]
    
    return GALLERY["generiche"]

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # Pulizia forzata per eliminare i vecchi post di Larry David
    if os.path.exists(HISTORY_FILE):
        try: os.remove(HISTORY_FILE)
        except: pass

    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore feed: {e}")
        return

    print(f"Articoli trovati: {len(feed.entries)}")
    new_posts_counter = 0

    for i, entry in enumerate(feed.entries[:5]):
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Elaborazione: {title}")
        img_url = select_best_image(title)

        message = f"🔥 *{title}*\n\n👉 *Leggi la notizia completa qui:* {link}\n\n#onepiece #anime #manga"
        
        try:
            # Invio tramite URL statico e sicuro
            await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="Markdown")
            print(" -> Inviato!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
