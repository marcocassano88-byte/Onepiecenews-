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
LOCAL_IMAGE = "copertina.jpg"

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
    print(f"Trovati {len(feed.entries)} articoli. Elaborazione...")

    # Inviamo i post sul canale
    for entry in feed.entries[:15]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        source = entry.get("source", {}).get("text", "Google News")
        
        if not title or not link:
            continue
            
        uid = make_id(title)
        if uid in posted_ids:
            continue

        clean_title = re.sub(r'\s+-\s+[^ ]+$', '', title).strip()
        safe_title = clean_for_html(clean_title)

        message = (
            f"🔥 <b>{safe_title}</b>\n\n"
            f"📰 Fonte: {clean_for_html(source)}\n\n"
            f"👉 <a href='{link}'>CLICCA QUI PER LEGGERE LA NOTIZIA</a>\n\n"
            f"#onepiece #anime #manga #news"
        )

        try:
            # Se l'immagine locale esiste, la carichiamo direttamente nel messaggio di Telegram
            if os.path.exists(LOCAL_IMAGE):
                with open(LOCAL_IMAGE, 'rb') as photo_file:
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=photo_file,
                        caption=message,
                        parse_mode="HTML"
                    )
            else:
                # Emergenza estrema senza immagine
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            
            print(f" -> [OK] Inviato con successo: {clean_title[:35]}...")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
            posted_ids.add(uid)
            
            total_uploaded += 1
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f" -> Errore durante l'invio: {e}")

    print(f"\n[FINE] Operazione completata. Inviati: {total_uploaded} post.")

if __name__ == "__main__":
    asyncio.run(main())
