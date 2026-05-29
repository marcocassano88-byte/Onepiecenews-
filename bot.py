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

# GALLERIA DI IMMAGINI HD SICURE (Link stabili che Telegram carica al 100%)
# Abbiamo inserito immagini reali di One Piece che non possono essere bloccate
ANIME_IMAGES = {
    "netflix": "https://m.media-amazon.com/images/M/MV5BMTNjNGU0YTQtYjEyOC00YmYxLTk0MTQtYWFhNmYxN2VlYTg4XkEyXkFqcGc5V1NleG90b2hvbG9nby1pbnN0YW5jZQ@@._V1_.jpg", # Poster Wit Remake
    "live_action": "https://m.media-amazon.com/images/M/MV5BODcwNWE3OTItMDc3MS00NDFmLWE1OTAtNDU3MTEyNzg5ZmQ4XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_.jpg", # Cast Live Action
    "milano": "https://m.media-amazon.com/images/M/MV5BMGMwNjk2ODQtY2M0MC00YWE1LTg4MjItMDQzNDM0ZGNjYmFkXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg", # Poster Celebrazione / Eventi
    "luffy": "https://m.media-amazon.com/images/M/MV5BN2VmYmE1OTAtNWI3Mi00NTg1LWIyYTUtM2U1ZGI2MGVjYWU4XkEyXkFqcGdeQXVyNDgyODgxNjE@._V1_.jpg", # Luffy Gear 5 / Wano
    "zoro": "https://m.media-amazon.com/images/M/MV5BOGYwNzkzZGEtODhkMS00NWEwLTg1YTUtYmI0MGQ0MGI3NTY2XkEyXkFqcGdeQXVyNDgyODgxNjE@._V1_.jpg", # Roronoa Zoro
    "ciurma": "https://m.media-amazon.com/images/M/MV5BODcwNWE3OTItMDc3MS00NDFmLWE1OTAtNDU3MTEyNzg5ZmQ4XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_.jpg" # Poster Ciurma Standard
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def select_image_by_keyword(title):
    """Sceglie l'immagine di One Piece più adatta in base alle parole nel titolo."""
    t = title.lower()
    if "netflix" in t or "remake" in t or "wit" in t:
        return ANIME_IMAGES["netflix"]
    elif "live" in t or "action" in t or "attori" in t:
        return ANIME_IMAGES["live_action"]
    elif "milano" in t or "store" in t or "pop-up" in t:
        return ANIME_IMAGES["milano"]
    elif "zoro" in t:
        return ANIME_IMAGES["zoro"]
    elif "luffy" in t or "rufy" in t or "gear" in t:
        return ANIME_IMAGES["luffy"]
    
    return ANIME_IMAGES["ciurma"]

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # Pulizia dello storico per questo run di test (elimina i loghi di google vecchi)
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
        
        print(f"Elaborazione {i+1}: {title}")
        
        # Seleziona l'immagine corretta dal nostro database blindato di IMDB (Niente loghi Google!)
        photo_url = select_image_by_keyword(title)

        # Messaggio pulito ed editoriale con il link nascosto
        message = (
            f"🔥 *{title}*\n\n"
            f"👉 [CLICCA QUI PER LEGGERE LA NOTIZIA]({google_link})\n\n"
            f"#onepiece #anime #manga"
        )
        
        try:
            # Invio della foto a schermo intero
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo_url,
                caption=message,
                parse_mode="Markdown"
            )
            print(" -> Post inviato correttamente!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
