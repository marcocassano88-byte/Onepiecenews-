import os
import asyncio
import hashlib
import requests
import feedparser
import html
import re
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Feed stabile di Google News Italia su One Piece
RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+when:7d&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# LISTA DI IMMAGINI HD IMMUNI AI BLOCCHI (Ospitate su server liberi o CDN ufficiali)
ANIME_IMAGES = [
    "https://i.imgur.com/8QZ7Xm7.jpeg",  # Luffy Gear 5 HD
    "https://i.imgur.com/M6LgO9b.jpeg",  # Ciurma di Cappello di Paglia Wano
    "https://i.imgur.com/uY6qA4z.jpeg",  # Zoro e Sanji HD
    "https://i.imgur.com/H1XU8R7.jpeg",  # One Piece Remake Wit Studio
    "https://i.imgur.com/vH9Z3pL.jpeg",  # Luffy Egghead Arc
    "https://i.imgur.com/Tkb3mE2.jpeg"   # I tre fratelli: Luffy, Ace, Sabo
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_for_html(text):
    if not text: return ""
    return html.escape(text.strip())

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali BOT_TOKEN o CHAT_ID assenti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    print("--- RECUPERO NOTIZIE IN CORSO ---")
    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore connessione feed: {e}")
        return

    if not feed.entries:
        print("Nessuna notizia trovata.")
        return

    total_uploaded = 0
    img_index = 0
    print(f"Trovati {len(feed.entries)} articoli. Elaborazione...")

    # Carica fino a 15 post per riempire velocemente il canale
    for entry in feed.entries[:15]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        source = entry.get("source", {}).get("text", "Google News")
        
        if not title or not link:
            continue
            
        uid = make_id(title)
        if uid in posted_ids:
            continue

        # Pulizia estetica del titolo eliminando il nome del sito alla fine
        clean_title = re.sub(r'\s+-\s+[^ ]+$', '', title).strip()
        safe_title = clean_for_html(clean_title)

        # Genera il testo del messaggio
        message = (
            f"🔥 <b>{safe_title}</b>\n\n"
            f"📰 Fonte: {clean_for_html(source)}\n\n"
            f"👉 <a href='{link}'>CLICCA QUI PER LEGGERE LA NOTIZIA</a>\n\n"
            f"#onepiece #anime #manga #news"
        )

        # Seleziona l'immagine dalla galleria a rotazione
        selected_photo = ANIME_IMAGES[img_index % len(ANIME_IMAGES)]

        try:
            # Invio della foto a tutto schermo
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=selected_photo,
                caption=message,
                parse_mode="HTML"
            )
            print(f" -> [OK] Inviato con successo: {clean_title[:35]}...")
            
            # Aggiorna lo storico e l'indice dell'immagine
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
            posted_ids.add(uid)
            
            total_uploaded += 1
            img_index += 1
            await asyncio.sleep(5)  # Pausa di sicurezza anti-ban
            
        except Exception as e:
            print(f" -> Errore durante l'invio: {e}")

    print(f"\n[FINE] Operazione completata. Inviati: {total_uploaded} post con immagini HD.")

if __name__ == "__main__":
    asyncio.run(main())
