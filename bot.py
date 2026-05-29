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
    
    # Pulizia dello storico per questo invio di test
    if os.path.exists(HISTORY_FILE):
        try: os.remove(HISTORY_FILE)
        except: pass

    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"Errore feed: {e}")
        return

    print(f"Articoli trovati nel feed: {len(feed.entries)}")
    new_posts_counter = 0

    for i, entry in enumerate(feed.entries[:5]):
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Elaborazione {i+1}: {title}")

        # Costruiamo il post. Mettendo il link come prima cosa, Telegram
        # genererà AUTOMATICAMENTE la grande anteprima con la foto reale dell'articolo.
        message = f"📰 *{title}*\n\n👉 *Continua a leggere la notizia su:* {link}\n\n#onepiece #anime #manga"
        
        try:
            # Inviamo un messaggio di testo abilitando l'anteprima web con foto grande
            await bot.send_message(
                chat_id=CHAT_ID, 
                text=message, 
                parse_mode="Markdown",
                disable_web_page_preview=False # Questo forza Telegram a mostrare la foto reale della fonte!
            )
            print(" -> Post inviato con anteprima fotografica automatica!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{make_id(title)}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> Errore d'invio: {e}")

    print(f"\nFine sessione. Inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
