import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
from PIL import Image, ImageDraw

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

def create_solid_image(category_color):
    """Genera un'immagine nativa colorata direttamente in memoria senza usare link esterni."""
    # Crea un rettangolo moderno 16:9 (800x450) con il colore della categoria
    img = Image.new("RGB", (800, 450), color=category_color)
    d = ImageDraw.Draw(img)
    
    # Aggiunge un bordo interno elegante stile poster
    d.rectangle([(20, 20), (780, 430)], outline="#FFFFFF", width=3)
    
    # Salva il file in un flusso di byte in memoria
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def get_color_by_title(title):
    """Assegna un colore di sfondo unico in base all'argomento della notizia."""
    t = title.lower()
    if "netflix" in t or "remake" in t or "wit" in t:
        return "#E50914"  # Rosso Netflix
    elif "milano" in t or "store" in t or "pop-up" in t:
        return "#FF9F43"  # Arancione Eventi / Milano
    elif "luffy" in t or "rufy" in t or "gear" in t:
        return "#EE5253"  # Rosso Luffy
    elif "zoro" in t:
        return "#10AC84"  # Verde Zoro
    elif "sanji" in t:
        return "#2E86DE"  # Blu Sanji
    
    return "#222f3e"  # Blu Notte scuro generico per le altre notizie

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("CRITICO: Credenziali BOT_TOKEN o CHAT_ID mancanti!")
        return

    print("Avvio il Bot Telegram...")
    bot = Bot(token=BOT_TOKEN)
    
    print(f"Scaricamento feed...")
    try:
        response = requests.get(RSS_FEED, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"ERRORE durante lo scaricamento del feed: {e}")
        return
    
    if not feed.entries:
        print("ATTENZIONE: Il feed è vuoto.")
        return

    print(f"Articoli totali trovati nel feed: {len(feed.entries)}")
    new_posts_counter = 0

    for i, entry in enumerate(feed.entries[:10]):
        print(f"\n--- Elaborazione articolo {i+1} ---")
        
        title = entry.get("title", "Nuova notizia One Piece")
        link = entry.get("link", "https://news.google.com")
        
        print(f"Titolo: {title}")
        uid = make_id(title)

        # === FORZATURA RESET ATTIVA (Invia tutto subito per sbloccare il canale) ===
        # if os.path.exists(HISTORY_FILE):
        #     with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        #         if uid in f.read():
        #             print("Articolo già presente nello storico. Salto.")
        #             continue

        print("Generazione immagine nativa...")
        color = get_color_by_title(title)
        image_stream = create_solid_image(color)
        image_stream.name = "news_image.jpg"

        print("Invio in corso a Telegram...")
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n#onepiece #anime #manga"
        
        try:
            # Inviamo l'immagine come file di byte puro, Telegram non può rifiutarlo
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message)
            print(" -> SUCCESSO: Post inviato!")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(4)
        except Exception as e:
            print(f" -> ERRORE Telegram: {e}")

    print(f"\nSessione conclusa. Post inviati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
