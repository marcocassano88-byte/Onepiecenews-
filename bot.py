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

# Galleria con immagini REALI e STABILI (Ospitate su server sicuri)
GALLERY = {
    "netflix": "https://images.justwatch.com/poster/306734135/s592/the-one-piece.jpg", 
    "live_action": "https://images.justwatch.com/poster/306548545/s592/one-piece-2023.jpg", 
    "milano": "https://m.media-amazon.com/images/I/719FvU9WunL._AC_UF894,1000_QL80_.jpg", 
    "generiche": "https://m.media-amazon.com/images/M/MV5BODcwNWE3OTItMDc3MS00NDFmLWE1OTAtNDU3MTEyNzg5ZmQ4XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_.jpg" 
}

LUFFY_IMG = "https://m.media-amazon.com/images/I/719FvU9WunL._AC_UF894,1000_QL80_.jpg"
ZORO_IMG = "https://m.media-amazon.com/images/I/71MepNqCHYL._AC_UF894,1000_QL80_.jpg"
SANJI_IMG = "https://m.media-amazon.com/images/I/71v1R8qL7mL._AC_UF894,1000_QL80_.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def generate_dynamic_hashtags(title):
    """Analizza il titolo e genera hashtag specifici e coerenti con la notizia."""
    t = title.lower()
    # Hashtag di base che devono esserci sempre
    tags = ["#onepiece", "#anime"]
    
    # Controlli dinamici basati sulle parole chiave nel titolo
    if "manga" in t: tags.append("#manga")
    if "netflix" in t: tags.append("#netflix")
    if "remake" in t or "wit" in t: tags.extend(["#theonepiece", "#remake"])
    if "live" in t or "action" in t or "attori" in t or "cast" in t: tags.append("#liveaction")
    if "milano" in t or "store" in t or "pop-up" in t: tags.extend(["#onepiecemilano", "#milano"])
    if "luffy" in t or "rufy" in t: tags.append("#luffy")
    if "gear 5" in t or "gear fifth" in t or "nika" in t: tags.extend(["#gear5", "#nika"])
    if "zoro" in t: tags.append("#zoro")
    if "sanji" in t: tags.append("#sanji")
    if "oda" in t or "eiichiro" in t: tags.append("#eiichirooda")
    if "crunchyroll" in t: tags.append("#crunchyroll")
    if "spoiler" in t or "capitolo" in t: tags.append("#opspoiler")
    
    # Se per qualche motivo l'articolo non rientra in nessuna categoria, aggiunge #manga di sicurezza
    if len(tags) < 3 and "#manga" not in tags:
        tags.append("#manga")
        
    # Restituisce i primi 5 hashtag uniti da uno spazio
    return " ".join(tags[:5])

def select_best_image(title):
    t = title.lower()
    if "netflix" in t or "remake" in t or "wit" in t:
        return GALLERY["netflix"]
    elif "live" in t or "action" in t or "attori" in t:
        return GALLERY["live_action"]
    elif "milano" in t or "store" in t or "pop-up" in t:
        return GALLERY["milano"]
    elif "zoro" in t:
        return ZORO_IMG
    elif "sanji" in t:
        return SANJI_IMG
    elif "luffy" in t or "rufy" in t or "gear" in t:
        return LUFFY_IMG
    return GALLERY["generiche"]

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # Svuota lo storico locale per questo run così vedi subito l'effetto dei nuovi hashtag
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
        
        # Generiamo gli hashtag intelligenti per questa specifica notizia
        custom_hashtags = generate_dynamic_hashtags(title)

        message = f"🔥 *{title}*\n\n👉 *Leggi la notizia completa qui:* {link}\n\n{custom_hashtags}"
        
        try:
            await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="Markdown")
            print(" -> Post inviato con successo!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
