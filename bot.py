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

# I 4 profili di X fondamentali per One Piece (Scrivili esattamente così)
ACCOUNT_X = ["pewpiece", "sandman_AP", " someonesanz", "MangaMoguraRE"]

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
        # Cerca l'immagine dentro la descrizione del feed (Nitter inserisce i tag <img>)
        description = feed_entry.get("description", "")
        if not description:
            return None
            
        soup = BeautifulSoup(description, "html.parser")
        img_tag = soup.find("img")
        
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
            
            # Se il link è relativo, lo sistemiamo
            if img_url.startswith("/"):
                img_url = "https://nitter.net" + img_url
                
            # Scarica l'immagine localmente sul server per bypassare i blocchi di Telegram
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
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    
    posted_ids = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            posted_ids = set(line.strip() for line in f)

    total_uploaded = 0

    # Scansiona i 4 canali scelti uno alla volta
    for username in ACCOUNT_X:
        print(f"\n--- SCANSIONE PROFILO X: @{username} ---")
        
        # Usiamo un'istanza pubblica e stabile di Nitter per leggere X
        rss_url = f"https://nitter.net/{username}/rss"
        
        try:
            response = requests.get(rss_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                # Prova un server alternativo se il primo è sovraccarico
                rss_url = f"https://nitter.cz/{username}/rss"
                response = requests.get(rss_url, headers=HEADERS, timeout=15)
                
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"Impossibile leggere il profilo @{username}: {e}")
            continue

        if not feed.entries:
            continue

        # Prende gli ultimi 3 tweet di ogni profilo per rimanere aggiornatissimo
        for entry in feed.entries[:3]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            
            if not title:
                continue
                
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in posted_ids:
                continue

            # Pulizia del testo del Tweet
            tweet_text = clean_tweets_text(title)
            
            # Costruiamo il layout per Telegram da canale di punta
            message = (
                f"📢 <b>ULTIM'ORA DA X</b> (via @{username})\n\n"
                f"{tweet_text}\n\n"
                f"🔗 <a href='{link}'>Apri il post originale su X</a>\n\n"
                f"#onepiece #leaks #anime #manga"
            )

            # Controlla se c'è una foto nel tweet e la scarica
            photo_path = download_x_image(entry)

            try:
                if photo_path and os.path.exists(photo_path):
                    # SE C'È LA FOTO: Spedisci foto + testo coordinato
                    with open(photo_path, 'rb') as photo_file:
                        await bot.send_photo(chat_id=CHAT_ID, photo=photo_file, caption=message, parse_mode="HTML")
                    print(f" -> [OK] Inviato tweet con la sua immagine originale.")
                    os.remove(TEMP_IMAGE)
                else:
                    # SE NON C'È LA FOTO: Manda solo il testo, massima coerenza
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
                    print(f" -> [OK] Inviato tweet di solo testo (nessuna foto presente).")

                # Salva nello storico
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{uid}\n")
                posted_ids.add(uid)
                
                total_uploaded += 1
                await asyncio.sleep(5) # Protezione anti-flood
                
            except Exception as e:
                print(f" -> Errore d'invio del tweet: {e}")
                if os.path.exists(TEMP_IMAGE):
                    os.remove(TEMP_IMAGE)

    print(f"\n[FINE] Aggiornamento da X completato. Post inviati: {total_uploaded}")

if __name__ == "__main__":
    asyncio.run(main())
