import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Nuovo feed italiano stabile e senza blocchi anti-bot
RSS_FEED = "https://www.animeclick.it/rss/anime"
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted = set(line.strip() for line in f if line.strip())

    print("Scaricamento feed AnimeClick...")
    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore download feed: {e}")
        return

    if not feed.entries:
        print("Impossibile leggere il feed.")
        return

    print(f"Trovati {len(feed.entries)} articoli generali.")
    new_posts_counter = 0

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        
        # Filtro stringente: pubblichiamo solo se si parla di One Piece
        if "one piece" not in title.lower():
            continue
            
        uid = make_id(title)

        if uid in posted:
            continue

        print(f"Trovata nuova notizia: {title}")
        message = f"🔥 *{title}*\n\n👉 *Leggi i dettagli su AnimeClick:*\n{link}\n\n#onepiece #anime #manga"
        
        try:
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=message, 
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            print(" -> Inviato!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)
            
            if new_posts_counter >= 3: # Limite di sicurezza per run
                break
                
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"Fine. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
