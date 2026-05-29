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

# I 4 PROFILI FONTE IN ITALIANO SU X
ACCOUNT_X = ["OP_Spoiler_IT", "OnePiece_It", "OPLiveActionIT", "BikeAndRaft"]

HISTORY_FILE = "posted_urls.txt"
TEMP_IMAGE = "temp_x_image.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_tweets_text(text):
    """Pulisce il testo del tweet rimuovendo link interni di X o Nitter"""
    if not text: return ""
    # Rimuove i link alla fine del tweet che portano all'immagine o al tweet stesso
    text = re.sub(r'https?://\S+', '', text)
    return html.escape(text.strip())

def download_x_image(feed_entry):
    """Cerca se nel feed del tweet c'è un'immagine allegata e la scarica"""
    try:
        description = feed_entry.get("description", "")
        if not description:
            return None
            
        soup = BeautifulSoup(description, "html.parser")
        img_tag = soup.find("img")
        
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
            
            # Se il link è relativo rispetto all'istanza Nitter, lo sistemiamo
            if img_url.startswith("/"):
                img_url = "https://nitter.net" + img_url
                
            # Scarica l'immagine localmente sul server temporaneo di GitHub
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

    # Scansiona i 4 canali italiani uno alla volta
    for username in ACCOUNT_X:
        print(f"\n--- SCANSIONE PROFILO X: @{username} ---")
        
        # Istanza Nitter principale per recuperare i post
        rss_url = f"https://nitter.net/{username}/rss"
        
        try:
            response = requests.get(rss_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                # Istanza di riserva se la prima risponde con errore
                rss_url = f"https://nitter.cz/{username}/rss"
                response = requests.get(rss_url, headers=HEADERS, timeout=15)
                
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Impossibile leggere il profilo @{username}: {e}")
            continue

        if not feed.entries:
            print(f"Nessun post recente trovato per @{username}")
            continue

        # Elabora gli ultimi 3 post per ogni profilo per non intasare il canale
        for entry in feed.entries[:3]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            
            if not title:
                continue
                
            # Genera ID basato sul link unico del post per evitare duplicati
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids:
                continue

            # Pulizia estetica del testo del Tweet
            tweet_text = clean_tweets_text(title)
            
            # Formattazione professionale del post per Telegram
            message = (
                f"📢 <b>ULTIM'ORA DA X</b> (via @{username})\n\n"
                f"{tweet_text}\n\n"
                f"🔗 <a href='{link}'>Apri il post originale su X</a>\n\n"
                f"#onepiece #leaks #anime #manga #news"
            )

            # Tenta il download della foto originale attaccata al tweet
            photo_path = download_x_image(entry)

            try:
                if photo_path and os.path.exists(photo_path):
                    # COERENZA MASSIMA: Se c'è la foto originale, manda la foto
                    with open(photo_path, 'rb') as photo_file:
                        await bot.send_photo(chat_id=CHAT_ID, photo=photo_file, caption=message, parse_mode="HTML")
                    print(f" -> [OK] Inviato post con immagine originale.")
                    os.remove(TEMP_IMAGE)
                else:
                    # COERENZA MASSIMA: Se è solo testo, manda solo testo (Niente ripieghi)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
                    print(f" -> [OK] Inviato post di solo testo.")

                # Aggiorna lo storico
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(5) # Pausa di sicurezza anti-flood
                
            except Exception as e:
                print(f" -> Errore d'invio del post: {e}")
                if os.path.exists(TEMP_IMAGE):
                    os.remove(TEMP_IMAGE)

    print(f"\n[FINE] Aggiornamento completato. Nuovi post italiani caricati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
