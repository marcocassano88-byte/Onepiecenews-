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

# Immagine Jolly Roger di Crunchyroll sicura al 100% (non può fallire)
DEFAULT_IMAGE = "https://www.crunchyroll.com/imgs-repo/image/uploads/0bf1507d39cc5a5197825d10d02eb6b7.jpg"

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali mancanti nelle variabili d'ambiente.")
        return

    print("Avvio il Bot Telegram...")
    bot = Bot(token=BOT_TOKEN)
    
    print(f"Scaricamento feed da: {RSS_FEED}")
    feed = feedparser.parse(RSS_FEED)
    
    if not feed.entries:
        print("ATTENZIONE: Il feed RSS è completamente vuoto o irraggiungibile.")
        return

    print(f"Articoli totali trovati nel feed: {len(feed.entries)}")
    new_posts_counter = 0

    # Prendiamo i primi 10 articoli
    for i, entry in enumerate(feed.entries[:10]):
        print(f"\n--- Analisi articolo {i+1} ---")
        
        # Recupero sicuro dei dati con fallback se mancano i tag
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Titolo letto: {title}")
        print(f"Link letto: {link}")
        
        uid = make_id(title)
        print(f"ID generato: {uid}")

        # FORZATURA RESET COMPLETA: Commentato il blocco storico per forzare l'invio ora
        # if os.path.exists(HISTORY_FILE):
        #     with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        #         if uid in f.read():
        #             print("Articolo già presente nello storico. Salto.")
        #             continue

        print("Tento l'invio su Telegram...")
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n#onepiece #anime #manga"
        
        try:
            # Invio diretto senza scaricare l'immagine localmente
            await bot.send_photo(chat_id=CHAT_ID, photo=DEFAULT_IMAGE, caption=message)
            print(" -> SUCCESSO: Post inviato al canale!")
            
            # Scrittura nello storico
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
            
        except Exception as e:
            print(f" -> ERRORE durante l'invio a Telegram: {e}")

    print(f"\nSessione conclusa. Post totali inviati in questo run: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
