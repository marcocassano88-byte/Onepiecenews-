import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
from PIL import Image

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def create_fallback_image():
    """Genera un'immagine di riserva scura se l'articolo non ha una foto, senza usare link esterni."""
    img = Image.new("RGB", (800, 450), color="#1c1c24")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

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
        link = entry.get("link", "https://news.google.com")
        
        print(f"Elaborazione: {title}")
        
        # Cerchiamo di prendere l'immagine reale che Google News associa all'articolo
        source_img_url = None
        if "media_content" in entry:
            source_img_url = entry.media_content[0].get("url")
        elif "links" in entry:
            for l in entry.links:
                if "image" in l.get("type", ""):
                    source_img_url = l.get("href")
                    break

        image_stream = None
        if source_img_url:
            try:
                # Il server scarica l'immagine REALE della notizia
                img_res = requests.get(source_img_url, headers=HEADERS, timeout=10)
                if img_res.status_code == 200:
                    image_stream = io.BytesIO(img_res.content)
            except:
                pass

        # Se non c'è l'immagine o il download fallisce, usa la riserva interna vuota
        if not image_stream:
            image_stream = create_fallback_image()
            
        image_stream.name = "thumbnail.jpg"
        message = f"🔥 *{title}*\n\n👉 *Leggi la notizia completa qui:* {link}\n\n#onepiece #anime #manga"
        
        try:
            # Invio del file binario scaricato. Telegram DEVE accettarlo perché è un file locale, non un link.
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message, parse_mode="Markdown")
            print(" -> Inviato!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio definitivo: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
