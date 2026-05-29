import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
import re
from PIL import Image, ImageDraw

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

# User-Agent reale per evitare che i siti di news blocchino il bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def get_real_article_image(google_rss_link):
    """Trova l'immagine reale dell'articolo seguendo il reindirizzamento di Google News."""
    try:
        # 1. Segui il link di Google News per trovare il sito reale
        res = requests.get(google_rss_link, headers=HEADERS, timeout=5)
        real_url = res.url
        
        # 2. Scarica la pagina reale
        page_res = requests.get(real_url, headers=HEADERS, timeout=5)
        html = page_res.text
        
        # 3. Cerca il tag Open Graph (og:image) usato da tutti i giornali per i social
        image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
        if not image_match:
            image_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
            
        if image_match:
            img_url = image_match.group(1)
            # Scarica l'immagine reale della notizia
            img_data = requests.get(img_url, headers=HEADERS, timeout=5).content
            
            # Verifica che sia un'immagine valida prima di restituirla
            img = Image.open(io.BytesIO(img_data))
            img.verify()
            
            img_stream = io.BytesIO(img_data)
            img_stream.seek(0)
            return img_stream
    except:
        pass
    return None

def generate_news_card(title):
    """Crea un'immagine personalizzata con il titolo se non viene trovata un'immagine reale."""
    img = Image.new("RGB", (800, 450), color="#1a1a1a")
    d = ImageDraw.Draw(img)
    
    # Decorazione estetica bordi (Stile One Piece scuro/arancio)
    d.rectangle([(15, 15), (785, 435)], outline="#E74C3C", width=4)
    d.rectangle([(25, 25), (775, 425)], outline="#F39C12", width=2)
    
    # Tag del canale in alto
    d.text((40, 40), "ONE PIECE ITALIA NEWS", fill="#F39C12")
    
    # Spezza il titolo per farlo stare nell'immagine senza font esterni
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        if len(" ".join(current_line + [word])) * 12 > 700:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    lines.append(" ".join(current_line))
    
    # Scrivi il testo riga per riga
    y_text = 150
    for line in lines[:5]:
        d.text((50, y_text), line, fill="#FFFFFF")
        y_text += 45
        
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    return img_byte_arr

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "netflix" in t or "remake" in t: tags.append("#netflix")
    if "milano" in t or "pop up" in t: tags.append("#onepiecemilano")
    return " ".join(tags)

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: Credenziali mancanti.")
        return

    bot = Bot(token=BOT_TOKEN)
    feed = feedparser.parse(RSS_FEED)
    new_posts_counter = 0

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        uid = make_id(title)

        # ⚠️ MODIFICA DI TEST: Commentato temporaneamente per forzare l'invio dei post vecchi
        # if uid in posted:
        #     continue

        print(f"Elaborazione: {title}")
        
        # Prova a prendere l'immagine vera del giornale
        image_stream = get_real_article_image(link)
        is_failsafe = False
        
        # Se fallisce, genera la copertina grafica con il titolo scritto sopra
        if not image_stream:
            print(f"Immagine nativa non trovata. Genero copertina grafica.")
            image_stream = generate_news_card(title)
            is_failsafe = True

        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"

        try:
            image_stream.name = "news_image.jpg" if not is_failsafe else "news_card.jpg"
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message)
            print(f"Pubblicato con successo: {title}")
            
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Errore invio: {e}")

    print(f"Fine sessione. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
    
