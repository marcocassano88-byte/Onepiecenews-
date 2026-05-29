import os
import asyncio
import hashlib
import requests
import feedparser
import html
from telegram import Bot
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# FONTI RSS AFFIDABILI E SEMPRE ACCESSIBILI
FONTI = [
    "https://www.animeclick.it/rss/manga",
    "https://www.everyeye.it/feed/feed_anime.xml",
    "https://mangaforever.net/feed"
]

HISTORY_FILE = "posted_urls.txt"

async def main():
    bot = Bot(token=BOT_TOKEN)
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0
    TARGET_POSTS = 50

    for url in FONTI:
        if total_uploaded >= TARGET_POSTS: break
        
        feed = feedparser.parse(url)
        for entry in feed.entries[:30]:
            if total_uploaded >= TARGET_POSTS: break
            
            title = entry.get("title", "")
            link = entry.get("link", "")
            # Filtro per assicurarci che parli di One Piece
            if "one piece" not in title.lower(): continue
            
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids: continue

            message = f"📢 <b>{html.escape(title)}</b>\n\n🔗 <a href='{link}'>Leggi la notizia completa</a>"
            
            try:
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
                with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(f"{uid}\n")
                posted_ids.add(uid)
                total_uploaded += 1
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Errore: {e}")

    print(f"Riempimento completato: {total_uploaded} post inviati.")

if __name__ == "__main__":
    asyncio.run(main())
