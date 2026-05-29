import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# Immagine Jolly Roger sicura da Crunchyroll
DEFAULT_IMAGE = "https://www.crunchyroll.com/imgs-repo/image/uploads/0bf1507d39cc5a5197825d10d02eb6b7.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali BOT_TOKEN o CHAT_ID mancanti!")
        return

    print("Avvio il Bot Telegram...")
    bot = Bot(token=BOT_TOKEN)
    
    print(f"Scaricamento feed tramite requests (Bypass GitHub)...")
    try:
        # Scarichiamo la pagina fingendoci un browser reale per evitare blocchi geografici
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        print(f"Risposta di Google News ricevuta. Status Code: {response.status_code}")
        
        # Passiamo il testo scaricato a feedparser
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"ERRORE critico durante lo scaricamento del feed: {e}")
        return
    
    if not feed.entries:
        print("ATTENZIONE: Il feed è vuoto. Google sta bloccando la richiesta o la query non ha prodotto risultati.")
        # Stampiamo un pezzo della risposta per capire cosa vede Google
        print("Anteprima risposta del server:")
        print(response.text[:500])
        return

    print(f"Articoli totali trovati nel feed: {len(feed.entries)}")
    new_posts_counter = 0

    for i, entry in enumerate(feed.entries[:10]):
        print(f"\n--- Elaborazione articolo {i+1} ---")
        
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Titolo: {title}")
        uid = make_id(title)

        # FORZATURA RESET ATTIVA: manda tutto senza guardare la cronologia
        print("Invio in corso a Telegram...")
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n#onepiece #anime #manga"
        
        try:
            await bot.send_photo(chat_id=CHAT_ID, photo=DEFAULT_IMAGE, caption=message)
            print(" -> SUCCESSO: Post inviato!")
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> ERRORE Telegram: {e}")

    print(f"\nSessione conclusa. Post inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
