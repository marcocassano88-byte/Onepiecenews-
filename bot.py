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

FONTI = [
    "https://www.animeclick.it/rss/manga",
    "https://www.everyeye.it/feed/feed_anime.xml",
    "https://mangaforever.net/feed"
]

HISTORY_FILE = "posted_urls.txt"
TEMP_IMAGE = "temp_article_image.jpg"

def is_relevant(title, summary):
    keywords = ["one piece", "luffy", "oda", "manga", "anime", "spoiler", "capitolo"]
    text = f"{title.lower()} {summary.lower()}"
    return any(k in text for k in keywords)

def get_image_url(entry):
    # Cerca l'immagine nel feed
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    if 'enclosures' in entry and entry.enclosures:
        return entry.enclosures[0]['href']
    # Se non c'è, cerca nel contenuto HTML
    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img = soup.find("img")
    return img['src'] if img else None

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
        for entry in feed.entries[:40]:
            if total_uploaded >= TARGET_POSTS: break
            
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            
            if not is_relevant(title, summary): continue
            
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids: continue

            # Scarica immagine
            img_url = get_image_url(entry)
            photo_sent = False
            
            message = f"📢 <b>{html.escape(title)}</b>\n\n🔗 <a href='{link}'>Leggi la notizia completa</a>"

            try:
                if img_url:
                    response = requests.get(img_url, stream=True)
                    if response.status_code == 200:
                        with open(TEMP_IMAGE, 'wb') as f:
                            for chunk in response: f.write(chunk)
                        with open(TEMP_IMAGE, 'rb') as photo:
                            await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=message, parse_mode="HTML")
                        os.remove(TEMP_IMAGE)
                        photo_sent = True
                
                if not photo_sent:
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")

                with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(f"{uid}\n")
                posted_ids.add(uid)
                total_uploaded += 1
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Errore: {e}")

    print(f"Riempimento completato: {total_uploaded} post inviati.")

if __name__ == "__main__":
    asyncio.run(main())
