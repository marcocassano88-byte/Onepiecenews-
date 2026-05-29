import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Usiamo un'unica immagine HD di One Piece super stabile e hostata su server anime libero
CANDIDATE_IMAGE = "https://images.everyeye.it/img-notizie/one-piece-remake-wit-studio-cambiera-storia-v1-4-690226.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def download_image_as_file(url):
    """Scarica l'immagine localmente bypassando i blocchi e la trasforma in un file binario."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            img_io = io.BytesIO(res.content)
            img_io.name = "poster.jpg"
            return img_io
    except Exception as e:
        print(f" -> Errore download immagine: {e}")
    return None

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

    # Scarichiamo l'immagine REALE di One Piece prima di iniziare il ciclo dei post
    print("Download copertina di One Piece in corso...")
    photo_file = download_image_as_file(CANDIDATE_IMAGE)

    if not photo_file:
        print("CRITICO: Impossibile scaricare l'immagine di base. Interrompo.")
        return

    for i, entry in enumerate(feed.entries[:5]):
        title = entry.get("title", "Nuova notizia One Piece")
        google_link = entry.get("link", "")
        
        print(f"Elaborazione {i+1}: {title}")

        message = (
            f"🔥 *{title}*\n\n"
            f"👉 [CLICCA QUI PER LEGGERE LA NOTIZIA]({google_link})\n\n"
            f"#onepiece #anime #manga"
        )
        
        try:
            # Riportiamo il puntatore del file in memoria all'inizio per ogni invio
            photo_file.seek(0)
            
            # Inviamo il FILE FISICO, non il link. Telegram non può rifiutarlo.
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo_file,
                caption=message,
                parse_mode="Markdown"
            )
            print(" -> Post inviato con successo!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio definitivo: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
