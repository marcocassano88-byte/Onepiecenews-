
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

# ACCOUNT ITALIANI PULITI AL 100% SENZA SPAZI NASCOSTI
ACCOUNT_X = ["OP_Spoiler_IT", "OnePiece_It", "OPLiveActionIT", "BikeAndRaft"]

HISTORY_FILE = "posted_urls.txt"
TEMP_IMAGE = "temp_x_image.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_tweets_text(text):
    if not text: return ""
    text = re.sub(r'https?://\S+', '', text)
    return html.escape(text.strip())

def download_x_image(feed_entry):
    try:
        description = feed_entry.get("description", "")
        if not description:
            return None
            
        soup = BeautifulSoup(description, "html.parser")
        img_tag = soup.find("img")
        
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
            
            if img_url.startswith("/"):
                img_url = "https://nitter.net" + img_url
                
            img_res = requests.get(img_url, headers=HEADERS, timeout=10)
            if img_res.status_code == 200:
                with open(TEMP_IMAGE, "wb") as f:
                    f.write(img_res.content)
                return TEMP_IMAGE
    except Exception as e:
        print(f" -> Errore download immagine da X: {e}")
    return None

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali BOT_TOKEN o CHAT_ID mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0
    TARGET_POSTS = 50  # Obiettivo di riempimento iniziale

    for username in ACCOUNT_X:
        if total_uploaded >= TARGET_POSTS:
            break
            
        print(f"--- SCANSIONE MASSICCIA: @{username} ---")
        rss_url = f"https://nitter.net/{username}/rss"
        
        try:
            response = requests.get(rss_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                rss_url = f"https://nitter.cz/{username}/rss"
                response = requests.get(rss_url, headers=HEADERS, timeout=15)
                
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Impossibile leggere il profilo @{username}: {e}")
            continue

        if not feed.entries:
            print(f"Nessun post trovato per @{username}")
            continue

        for entry in feed.entries[:25]:
            if total_uploaded >= TARGET_POSTS:
                break

            title = entry.get("title", "")
            link = entry.get("link", "")
            
            if not title:
                continue
                
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids:
                continue

            tweet_text = clean_tweets_text(title)
            
            message = (
                f"📢 <b>ULTIM'ORA DA X</b> (via @{username})\n\n"
                f"{tweet_text}\n\n"
                f"🔗 <a href='{link}'>Apri il post originale su X</a>\n\n"
                f"#onepiece #leaks #anime #manga #news"
            )

            photo_path = download_x_image(entry)

            try:
                if photo_path and os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo_file:
                        await bot.send_photo(chat_id=CHAT_ID, photo=photo_file, caption=message, parse_mode="HTML")
                    print(f" -> [{total_uploaded + 1}/{TARGET_POSTS}] Post inviato con immagine.")
                    os.remove(TEMP_IMAGE)
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
                    print(f" -> [{total_uploaded + 1}/{TARGET_POSTS}] Post inviato di solo testo.")

                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(4)
                
            except Exception as e:
                print(f" -> Errore d'invio del post: {e}")
                if os.path.exists(TEMP_IMAGE):
                    os.remove(TEMP_IMAGE)

    print(f"\n[FINE] Riempimento completato. Inviati in questo ciclo: {total_uploaded} post.")

if __name__ == "__main__":
    asyncio.run(main())
