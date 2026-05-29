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

# Feed di Google News focalizzato su One Piece in Italia
RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+when:7d&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Immagine di backup ad alta risoluzione fissa
CANDIDATE_IMAGE = "https://images.everyeye.it/img-notizie/one-piece-remake-wit-studio-cambiera-storia-v1-4-690226.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_for_html(text):
    if not text: return ""
    return html.escape(text.strip())

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali BOT_TOKEN o CHAT_ID mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    print("--- LETTURA NOTIZIE DA GOOGLE NEWS ---")
    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore di connessione al feed: {e}")
        return

    if not feed.entries:
        print("Nessuna notizia recente trovata.")
        return

    total_uploaded = 0
    print(f"Trovati {len(feed.entries)} potenziali articoli. Inizio pubblicazione...")

    # Limitiamo a 15 elementi per evitare blocchi temporanei da Telegram
    for entry in feed.entries[:15]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        source = entry.get("source", {}).get("text", "Google News")
        
        if not title or not link:
            continue
            
        uid = make_id(title)
        if uid in posted_ids:
            continue

        # Pulizia del titolo dalla firma della testata alla fine (es: " - Wired")
        clean_title = re.sub(r'\s+-\s+[^ ]+$', '', title).strip()
        safe_title = clean_for_html(clean_title)

        # Costruzione del messaggio in HTML standard pulito
        message = (
            f"🔥 <b>{safe_title}</b>\n\n"
            f"📰 Fonte: {clean_for_html(source)}\n\n"
            f"👉 <a href='{link}'>CLICCA QUI PER LEGGERE LA NOTIZIA</a>\n\n"
            f"#onepiece #anime #manga #news"
        )

        try:
            # Inviamo l'immagine di copertina fissa per dare un aspetto grafico coerente a tutti i post
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=CANDIDATE_IMAGE,
                caption=message,
                parse_mode="HTML"
            )
            print(f" -> [OK] Post inviato: {clean_title[:30]}...")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
            posted_ids.add(uid)
            
            total_uploaded += 1
            await asyncio.sleep(5)  # Rispetto dei limiti anti-flood di Telegram
            
        except Exception as e:
            print(f" -> Errore d'invio su Telegram: {e}")

    print(f"\nProcedura completata. Nuovi post inviati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
