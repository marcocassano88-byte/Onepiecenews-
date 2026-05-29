import os
import asyncio
import hashlib
import requests
from telegram import Bot
import feedparser
import html
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ACCOUNTS = [
    "OP_Spoiler_IT",   
    "OnePiece_It",     
    "BikeAndRaft",     
    "OPLiveActionIT"   
]

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.perennialte.ch",
    "https://nitter.poast.org",
    "https://nitter.moomoo.me",
    "https://nitter.cz"
]

# GALLERIA DI IMMAGINI HD SICURE (Se il tweet è solo testo, usiamo una di queste a rotazione!)
FALLBACK_IMAGES = [
    "https://images.everyeye.it/img-notizie/one-piece-remake-wit-studio-cambiera-storia-v1-4-690226.jpg",
    "https://www.drcommodore.it/wp-content/uploads/2023/08/one-piece-gear-5.jpg",
    "https://images.everyeye.it/img-notizie/one-piece-netflix-ufficiale-scelta-attrice-miss-all-sunday-v1-730104.jpg",
    "https://images.everyeye.it/img-notizie/one-piece-manga-1111-pausa-tre-mesi-messaggio-oda-v1-703666.jpg"
]

HISTORY_FILE = "posted_tweets.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_for_html(text):
    if not text: return ""
    text = re.sub(r'https?://[^\s]+', '', text)
    return html.escape(text.strip())

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali mancanti!")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0
    fallback_index = 0

    for account in ACCOUNTS:
        print(f"\n--- Ricerca post per: @{account} ---")
        feed = None
        
        for instance in NIMTER_INSTANCES:
            url = f"{instance}/{account}/rss"
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    temp_feed = feedparser.parse(response.text)
                    if temp_feed.entries:
                        feed = temp_feed
                        break
            except:
                continue
        
        if not feed or not feed.entries:
            print(f"Server Nitter occupati per @{account}. Salto.")
            continue

        # Alziamo a 20 post storici ad account per spingere al massimo il riempimento
        for entry in feed.entries[:20]:
            raw_text = entry.get("title", "")
            if not raw_text:
                continue
                
            uid = make_id(raw_text)
            if uid in posted_ids:
                continue

            # 1. Cerchiamo l'immagine originale del tweet
            img_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                img_url = entry["media_thumbnail"][0]["url"]
            elif "enclosure" in entry:
                img_url = entry["enclosure"]["url"]

            # 2. SE NON C'È L'IMMAGINE, USIAMO LA NOSTRA GALLERIA DI COPPERTINE A ROTAZIONE
            if not img_url or not img_url.startswith("http"):
                img_url = FALLBACK_IMAGES[fallback_index % len(FALLBACK_IMAGES)]
                fallback_index += 1

            safe_text = clean_for_html(raw_text)
            if not safe_text:
                continue

            lines = safe_text.split('\n')
            title_line = lines[0]
            remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

            message = f"📢 <b>{title_line}</b>\n"
            if remaining_text:
                message += f"\n{remaining_text}\n"
            message += f"\n👉 <a href='https://x.com/{account}'>Apri il post originale su X</a>\n\n#{account.lower()} #onepiece #leak"

            try:
                # Ora inviamo SEMPRE come foto gigante a tutto schermo
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=img_url,
                    caption=message,
                    parse_mode="HTML"
                )
                print(f" -> [OK] Post inviato con immagine a schermo intero!")
                
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(6) # Pausa di sicurezza per fare le cose per bene
                
            except Exception as e:
                print(f" -> Errore d'invio finale: {e}")

    print(f"\n[FINE] Caricamento completato. Inviati in questo ciclo: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
