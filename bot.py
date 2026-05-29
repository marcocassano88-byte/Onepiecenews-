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

# 1. LISTA DEI PROFILI ITALIANI (Divisi per le categorie richieste)
ACCOUNTS = [
    "OP_Spoiler_IT",   # Leak & Spoiler capitoli
    "OnePiece_It",     # Notizie generali brand
    "BikeAndRaft",     # Teorie e approfondimenti
    "OPLiveActionIT"   # Notizie sul Live Action Netflix
]

HISTORY_FILE = "posted_tweets.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def clean_tweet_text(text):
    if not text: return ""
    text = re.sub(r'https?://nitter\.[^\s]+', '', text)
    text = re.sub(r'https?://twitter\.[^\s]+', '', text)
    text = re.sub(r'https?://x\.[^\s]+', '', text)
    return text.strip()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali mancanti nelle Actions!")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # IMPORTANTE: Per questo primo avvio di massa NON svuotiamo la cronologia se l'hai già avviato,
    # ma carichiamo tutto il blocco storico.
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0

    # Giriamo su tutti e 4 gli account italiani
    for account in ACCOUNTS:
        print(f"\n--- [Fase di Massa] Estrazione da: @{account} ---")
        rss_feed = f"https://nitter.poast.org/{account}/rss"
        
        try:
            response = requests.get(rss_feed, headers=HEADERS, timeout=15)
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Errore di connessione per {account}: {e}")
            continue

        if not feed.entries:
            print(f"Nessun post trovato per {account} (Nitter potrebbe essere sovraccarico), salto al prossimo...")
            continue

        # Prendiamo fino a 15 post storici per OGNI account per superare quota 50 post
        entries_to_process = feed.entries[:15]
        print(f"Trovati {len(feed.entries)} post. Ne elaboro fino a 15 storici...")

        for entry in entries_to_process:
            raw_text = entry.get("title", "")
            tweet_text = clean_tweet_text(raw_text)
            
            nitter_link = entry.get("link", "")
            tweet_link = nitter_link.replace("nitter.poast.org", "x.com")
            
            if not tweet_text:
                continue
                
            uid = make_id(tweet_text)
            
            # Evita di duplicare post se fai girare lo script più volte
            if uid in posted_ids:
                continue

            # Estrazione immagine nativa di X
            img_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                img_url = entry["media_thumbnail"][0]["url"]
            elif "enclosure" in entry:
                img_url = entry["enclosure"]["url"]

            # Formattazione testo (Prima riga in grassetto)
            lines = tweet_text.split('\n')
            title_line = lines[0]
            remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""
            
            message = f"📢 *{title_line}*\n"
            if remaining_text:
                message += f"\n{remaining_text}\n"
            message += f"\n👉 [Apri su X]({tweet_link})\n\n#{account.lower()} #onepiece #italy"

            try:
                if img_url:
                    await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                
                print(f" -> Postato con successo da @{account}")
                
                # Salva subito in cronologia
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                
                # PAUSA DI SICUREZZA GIGANTE: 6 secondi tra un post e l'altro.
                # Serve a non far arrabbiare Telegram durante il caricamento di massa!
                await asyncio.sleep(6)
                
            except Exception as e:
                print(f" -> Errore d'invio su Telegram: {e}")
                # Se Telegram ci dice che stiamo andando troppo veloci, si ferma per 30 secondi
                if "Too Many Requests" in str(e):
                    print("Attesa forzata anti-spam di 30 secondi...")
                    await asyncio.sleep(30)

    print(f"\n[COMPLETATO] Il canale è stato popolato con {total_uploaded} nuovi post storici!")

if __name__ == "__main__":
    asyncio.run(main())
