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

# LISTA DI EMERGENZA A ROTAZIONE: Se uno cade, il bot prova gli altri in automatico
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.perennialte.ch",
    "https://nitter.poast.org",
    "https://nitter.moomoo.me",
    "https://nitter.cz"
]

HISTORY_FILE = "posted_tweets.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_for_html(text):
    """Sostituisce i caratteri sensibili per evitare errori di parsing su Telegram."""
    if not text: return ""
    text = re.sub(r'https?://[^\s]+', '', text) # Rimuove i link di testo brutti
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

    for account in ACCOUNTS:
        print(f"\n--- Ricerca post per: @{account} ---")
        feed = None
        
        # Prova le istanze una per una finché una non risponde
        for instance in NITTER_INSTANCES:
            url = f"{instance}/{account}/rss"
            print(f"Provando server: {instance}...")
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    temp_feed = feedparser.parse(response.text)
                    if temp_feed.entries:
                        feed = temp_feed
                        print(f" -> Connesso con successo a {instance}!")
                        break
            except:
                continue
        
        if not feed or not feed.entries:
            print(f"Tutti i server Nitter sono temporaneamente occupati per @{account}. Salto.")
            continue

        print(f"Trovati {len(feed.entries)} post. Elaborazione...")

        # Prendiamo fino a 15 post storici per account per fare massa
        for entry in feed.entries[:15]:
            raw_text = entry.get("title", "")
            if not raw_text:
                continue
                
            uid = make_id(raw_text)
            if uid in posted_ids:
                continue

            # Estrazione immagine originale di X
            img_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                img_url = entry["media_thumbnail"][0]["url"]
            elif "enclosure" in entry:
                img_url = entry["enclosure"]["url"]

            # Puliamo e proteggiamo il testo usando lo standard HTML sicuro
            safe_text = clean_for_html(raw_text)
            if not safe_text or len(safe_text) < 10:
                continue

            # Dividiamo in righe per fare il titolo in grassetto
            lines = safe_text.split('\n')
            title_line = lines[0]
            remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

            # COSTRUZIONE POST IN HTML (Impossibile da rompere per Telegram)
            message = f"📢 <b>{title_line}</b>\n"
            if remaining_text:
                message += f"\n{remaining_text}\n"
            message += f"\n👉 <a href='https://x.com/{account}'>Apri il post originale su X</a>\n\n#{account.lower()} #onepiece #leak"

            try:
                if img_url and img_url.startswith("http"):
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=img_url,
                        caption=message,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                
                print(f" -> [OK] Inviato post su Telegram!")
                
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(5) # Pausa anti-spam
                
            except Exception as e:
                print(f" -> Errore d'invio finale: {e}")

    print(f"\n[FINE] Caricamento di massa completato. Post totali inviati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
