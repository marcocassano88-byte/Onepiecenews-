import os
import asyncio
import hashlib
import requests
import feedparser
import html
import re
from bs4 import BeautifulSoup
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ACCOUNT_X = ["OP_Spoiler_IT", "OnePiece_It", "OPLiveActionIT", "BikeAndRaft", "OnePieceItalia"]
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# --- PROVIAMO A USARE UN'ISTANZA DIVERSA DI NITTER ---
def get_rss_url(username):
    return f"https://nitter.cz/{username}/rss"

async def main():
    bot = Bot(token=BOT_TOKEN)
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0
    TARGET_POSTS = 50 

    for username in ACCOUNT_X:
        if total_uploaded >= TARGET_POSTS: break
            
        print(f"--- ANALISI FORZATA: @{username} ---")
        rss_url = get_rss_url(username)
        
        try:
            response = requests.get(rss_url, headers=HEADERS, timeout=20)
            feed = feedparser.parse(response.text)
            print(f" -> Trovati {len(feed.entries)} post nel feed.") # DEBUG
        except Exception as e:
            print(f" -> Errore connessione: {e}")
            continue

        for entry in feed.entries[:30]:
            if total_uploaded >= TARGET_POSTS: break
            
            title = entry.get("title", "")
            link = entry.get("link", "")
            
            # --- FILTRO DISABILITATO TEMPORANEAMENTE PER RIEMPIMENTO ---
            if not title: continue
                
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids: continue

            # Pulizia minima
            tweet_text = html.escape(title[:200])
            message = f"📢 <b>ULTIM'ORA ONE PIECE</b>\n\n{tweet_text}\n\n🔗 <a href='{link}'>Vedi su X</a>"

            try:
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=False)
                with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(f"{uid}\n")
                posted_ids.add(uid)
                total_uploaded += 1
                await asyncio.sleep(3)
            except Exception as e:
                print(f" -> Errore invio: {e}")

    print(f"\n[FINE] Riempimento tentato. Inviati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
