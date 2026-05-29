import os
import asyncio
import hashlib
import requests
from telegram import Bot
import json
import re

# Configurazione credenziali di GitHub
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# I nostri 4 account italiani di riferimento su X
ACCOUNTS = [
    "OP_Spoiler_IT",   
    "OnePiece_It",     
    "BikeAndRaft",     
    "OPLiveActionIT"   
]

HISTORY_FILE = "posted_tweets.txt"

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali BOT_TOKEN o CHAT_ID mancanti nelle Actions!")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0

    # Usiamo un'istanza alternativa di monitoraggio JSON per X, altamente performante
    for account in ACCOUNTS:
        print(f"\n--- Estrazione diretta da X: @{account} ---")
        
        # Sfruttiamo una costellazione di mirror alternativi per garantire la lettura dei dati
        url = f"https://nitter.privacydev.net/{account}/rss"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; x64) AppleWebKit/537.36"
        }
        
        try:
            import feedparser
            response = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Errore specchio principale per {account}: {e}. Provo specchio di riserva...")
            try:
                # Specchio secondario europeo ultra-veloce
                url_backup = f"https://nitter.perennialte.ch/{account}/rss"
                response = requests.get(url_backup, headers=headers, timeout=15)
                feed = feedparser.parse(response.text)
            except:
                print("Anche lo specchio di riserva è saturo. Salto l'account.")
                continue

        if not feed or not feed.entries:
            print(f"Nessun post raccolto da X per @{account}")
            continue

        print(f"Trovati {len(feed.entries)} post storici. Avvio filtraggio...")

        # Prendiamo fino a 15 post storici per account per fare massa sul canale vuoto
        for entry in feed.entries[:15]:
            tweet_text = entry.get("title", "")
            
            # Pulizia link interni di Twitter dal testo
            tweet_text = re.sub(r'https?://[^\s]+', '', tweet_text).strip()
            
            if not tweet_text or len(tweet_text) < 10:
                continue
                
            uid = make_id(tweet_text)
            if uid in posted_ids:
                continue

            # Estrazione immagine originale caricata su X
            img_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                img_url = entry["media_thumbnail"][0]["url"]
            elif "enclosure" in entry:
                img_url = entry["enclosure"]["url"]

            # Formattazione: Prima riga in GRASSETTO (Titolo stile bacheca)
            lines = tweet_text.split('\n')
            title_line = lines[0]
            remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

            message = f"📢 *{title_line}*\n"
            if remaining_text:
                message += f"\n{remaining_text}\n"
            message += f"\n👉 [Apri il post su X](https://x.com/{account})\n\n#{account.lower()} #onepiece #leak"

            try:
                if img_url:
                    # Spariamo l'immagine di X a tutto schermo
                    await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                
                print(f" -> Postato da @{account}: {title_line[:30]}...")
                
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(6) # Pausa anti-ban di Telegram
                
            except Exception as e:
                print(f" -> Errore d'invio Telegram: {e}")

    print(f"\n[FINE] Caricamento completato! Inviati in questo ciclo: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
