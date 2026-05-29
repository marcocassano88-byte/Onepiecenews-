import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot

# Configurazione credenziali da variabili d'ambiente GitHub
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Carica lo storico dei post già inviati per evitare duplicati
posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# 🖼️ DATABASE DI IMMAGINI REALI E COPERTINE FUNZIONANTI (URL Diretti)
# Se il titolo contiene una di queste parole, usa direttamente l'immagine associata.
ONE_PIECE_IMAGES = {
    "luffy": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800&auto=format&fit=crop&q=80", # Anime/Manga concept
    "zoro": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&auto=format&fit=crop&q=80",
    "netflix": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=800&auto=format&fit=crop&q=80", # Logo Netflix per news remake/live action
    "remake": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=800&auto=format&fit=crop&q=80",
    "live-action": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=800&auto=format&fit=crop&q=80",
    "milano": "https://images.unsplash.com/photo-1528731708534-816fe59f90cb?w=800&auto=format&fit=crop&q=80", # Pop-up store Milano
    "store": "https://images.unsplash.com/photo-1528731708534-816fe59f90cb?w=800&auto=format&fit=crop&q=80"
}

# Immagine di copertina generale di One Piece (Usata se non ci sono parole chiave specifiche)
DEFAULT_ONE_PIECE_IMAGE = "https://images.unsplash.com/photo-1560169897-fc0cdbdfa4d5?w=800&auto=format&fit=crop&q=80"

def get_image_url_for_post(title):
    """Scansiona il titolo e assegna l'URL dell'immagine corretta senza passare da Wikimedia."""
    t = title.lower()
    for key, url in ONE_PIECE_IMAGES.items():
        if key in t:
            return url
    return DEFAULT_ONE_PIECE_IMAGE

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "netflix" in t: tags.append("#netflix")
    return " ".join(tags)

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: BOT_TOKEN o CHAT_ID non configurati.")
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

        # Ottieni l'URL dell'immagine direttamente dal nostro database sicuro
        image_url = get_image_url_for_post(title)
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"

        try:
            # Telegram accetta direttamente un URL come stringa per il parametro photo!
            # Questo evita download, file temporanei, PIL, cache e problemi di memoria.
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=image_url,
                caption=message
            )
            print(f"Pubblicato con successo: {title}")
            
            # Salva nello storico per evitare duplicati
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5) # Pausa di sicurezza

        except Exception as e:
            print(f"Errore nell'invio del post '{title}': {e}")

    print(f"Task terminato. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
