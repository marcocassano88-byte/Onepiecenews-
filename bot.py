import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import re

# Configurazione credenziali di GitHub
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# I nostri 4 account italiani di riferimento
ACCOUNTS = [
    "OP_Spoiler_IT",   
    "OnePiece_It",     
    "BikeAndRaft",     
    "OPLiveActionIT"   
]

HISTORY_FILE = "posted_tweets.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_tweet_text(text):
    if not text: return ""
    # Pulisce i tag HTML che a volte spuntano nei feed
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://[^\s]+', '', text)
    return text.strip()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali mancanti nelle Actions!")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0

    for account in ACCOUNTS:
        print(f"\n--- Estrazione stabile da: @{account} ---")
        
        # Usiamo RSSHub, il servizio più potente e stabile del web per X
        rss_feed = f"https://rsshub.app/twitter/user/{account}"
        
        try:
            response = requests.get(rss_feed, headers=HEADERS, timeout=20)
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Errore di connessione per {account}: {e}")
            continue

        if not feed.entries:
            print(f"Nessun post estratto da rsshub per {account}. Provo un server alternativo...")
            # Server di riserva se il principale rallenta
            rss_feed_backup = f"https://moe.io.稳.rsshub.app/twitter/user/{account}"
            try:
                response = requests.get(rss_feed_backup, headers=HEADERS, timeout=15)
                feed = feedparser.parse(response.text)
            except:
                continue

        if not feed.entries:
            print(f"Nessun post disponibile per {account}")
            continue

        # Prendiamo fino a 15 post storici per iniziare a riempire il canale
        entries_to_process = feed.entries[:15]
        print(f"Trovati {len(feed.entries)} post. Ne elaboro fino a 15...")

        for entry in entries_to_process:
            raw_text = entry.get("description", entry.get("title", ""))
            tweet_text = clean_tweet_text(raw_text)
            
            tweet_link = f"https://x.com/{account}"
            
            if not tweet_text or len(tweet_text) < 5:
                continue
                
            uid = make_id(tweet_text)
            
            if uid in posted_ids:
                continue

            # Cerchiamo l'immagine allegata al post (se presente)
            img_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                img_url = entry["media_thumbnail"][0]["url"]
            
            # Se non la trova lì, proviamo a cercarla nel testo HTML del feed
            if not img_url and "description" in entry:
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry["description"])
                if img_match:
                    img_url = img_match.group(1)

            # Impostiamo il testo in modo leggibile
            lines = [line.strip() for line in tweet_text.split('\n') if line.strip()]
            if not lines: continue
            
            title_line = lines[0]
            remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""
            
            # Tagliamo se è biblico per evitare errori di Telegram
            if len(remaining_text) > 600:
                remaining_text = remaining_text[:600] + "..."

            message = f"📢 *{title_line}*\n"
            if remaining_text:
                message += f"\n{remaining_text}\n"
            message += f"\n👉 [Apri su X]({tweet_link})\n\n#{account.lower()} #onepiece #italy"

            try:
                if img_url and img_url.startswith("http"):
                    await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                
                print(f" -> Postato con successo da @{account}")
                
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(5) # Antispam
                
            except Exception as e:
                print(f" -> Errore d'invio: {e}")
                if "Too Many Requests" in str(e):
                    await asyncio.sleep(25)

    print(f"\n[COMPLETATO] Caricamento di massa terminato! Inviati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
