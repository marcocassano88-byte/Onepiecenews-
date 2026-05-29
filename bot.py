import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
import re
from PIL import Image, ImageDraw

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def create_anime_banner(theme):
    """Genera una copertina geometrica a contrasto senza l'uso di font."""
    # Sfondo scuro principale (1024x576)
    img = Image.new("RGB", (1024, 576), color="#1A1A24")
    d = ImageDraw.Draw(img)
    
    # Colori del tema
    primary = theme["primary"]
    accent = theme["accent"]
    
    # Pannello laterale colorato dinamico (Stile interfaccia anime)
    d.rectangle([(0, 0), (300, 576)], fill=primary)
    
    # Linee geometriche di accento
    d.rectangle([(280, 0), (300, 576)], fill=accent)
    d.polygon([(300, 0), (450, 0), (300, 576)], fill=primary)
    d.polygon([(300, 576), (450, 576), (300, 0)], fill=accent)
    
    # Cornice interna elegante per il testo
    d.rectangle([(40, 40), (984, 536)], outline="#FFFFFF", width=3)
    
    # Salva in memoria RAM
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    return img_byte_arr

def get_theme_by_title(title):
    t = title.lower()
    # Mappatura dei colori basata sui personaggi/temi di One Piece
    if "netflix" in t or "remake" in t or "wit" in t:
        return {"primary": "#E50914", "accent": "#FFFFFF"}  # Rosso Netflix
    elif "milano" in t or "store" in t or "pop-up" in t:
        return {"primary": "#E67E22", "accent": "#F1C40F"}  # Arancio/Oro Milano
    elif "luffy" in t or "rufy" in t or "gear" in t:
        return {"primary": "#8E44AD", "accent": "#6C5CE7"}  # Viola Gear 5 / Nika
    elif "zoro" in t:
        return {"primary": "#16A085", "accent": "#2ECC71"}  # Verde Zoro
    elif "sanji" in t:
        return {"primary": "#2980B9", "accent": "#3498DB"}  # Blu Sanji
    
    return {"primary": "#2C3E50", "accent": "#BDC3C7"}  # Grigio pirata di default

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti!")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # Svuota lo storico per questo run specifico, così invia subito i post aggiornati
    if os.path.exists(HISTORY_FILE):
        try: os.remove(HISTORY_FILE)
        except: pass

    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore caricamento feed: {e}")
        return

    print(f"Articoli trovati: {len(feed.entries)}")
    new_posts_counter = 0

    for i, entry in enumerate(feed.entries[:5]):
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Elaborazione post {i+1}: {title}")
        
        # Genera il banner geometrico personalizzato (No Font = Zero errori)
        theme = get_theme_by_title(title)
        image_stream = create_anime_banner(theme)
        image_stream.name = "one_piece_news.jpg"

        # Il titolo viene formattato in grassetto direttamente nella didascalia di Telegram
        message = f"🔥 *{title}*\n\n👉 *Leggi la notizia completa qui:* {link}\n\n#onepiece #anime #manga"
        
        try:
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message, parse_mode="Markdown")
            print(" -> Inviato!")
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
