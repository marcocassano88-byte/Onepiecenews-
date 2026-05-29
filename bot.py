import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import re

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Immagine della ciurma a tutto schermo da usare come ruota di scorta se un sito non ha foto
FALLBACK_IMAGE = "https://images.everyeye.it/img-notizie/one-piece-remake-wit-studio-cambiera-storia-v1-4-690226.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def get_real_article_data(google_link):
    """Segue il redirect di Google per trovare il sito vero ed estrae l'immagine grande."""
    try:
        # Troviamo il link vero dell'articolo
        res = requests.get(google_link, headers=HEADERS, timeout=10)
        real_url = res.url
        
        # Cerchiamo l'immagine principale (Open Graph Image) nel codice del sito
        html = res.text
        img_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
        if not img_match:
            img_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
            
        if img_match:
            return real_url, img_match.group(1)
        return real_url, FALLBACK_IMAGE
    except:
        return google_link, FALLBACK_IMAGE

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
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
        google_link = entry.get("link", "")
        
        print(f"\nElaborazione {i+1}: {title}")
        
        # Estraiamo il link vero e l'immagine a tutto schermo dal sito della notizia
        real_link, big_image_url = get_real_article_data(google_link)
        print(f" -> Immagine trovata: {big_image_url}")

        # Formattazione del post pulita con il titolo in grassetto
        message = (
            f"🔥 *{title}*\n\n"
            f"👉 [CLICCA QUI PER LEGGERE LA NOTIZIA]({real_link})\n\n"
            f"#onepiece #anime #manga"
        )
        
        try:
            # Inviamo come FOTO REALE, così l'immagine sarà gigante a tutto schermo
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=big_image_url,
                caption=message,
                parse_mode="Markdown"
            )
            print(" -> Post con immagine gigante inviato!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
