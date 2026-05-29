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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def clean_title_for_search(title):
    """Rimuove il nome della testata giornalistica alla fine del titolo per ottimizzare la ricerca immagini."""
    cleaned = re.sub(r'\s*-\s*[^-\n]+$', '', title)
    return cleaned.strip()

def get_image_from_search(title):
    """Cerca un'immagine pertinente in tempo reale usando il motore di ricerca DuckDuckGo."""
    try:
        search_term = clean_title_for_search(title)
        print(f"Cerco immagine per: '{search_term}'")
        
        # Query di ricerca su DuckDuckGo Immagini
        url = "https://duckduckgo.com/iu/"
        params = {
            "q": search_term,
            "f": "1",
            "p": "1"
        }
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Estrae i link delle immagini dai risultati della ricerca
            image_urls = re.findall(r'image_url["\']:\s*["\'](http[s]?://[^"\']+)["\']', response.text)
            
            # Filtra ed evita loghi di Google News o immagini palesemente errate
            valid_urls = [u for u in image_urls if "lh3.googleusercontent" not in u and "google" not in u.lower()]
            
            # Tenta di scaricare una delle prime 3 immagini trovate
            for img_url in valid_urls[:3]:
                try:
                    img_res = requests.get(img_url, headers=HEADERS, timeout=7)
                    if img_res.status_code == 200:
                        # Verifica che sia un file immagine valido e non corrotto
                        img = Image.open(io.BytesIO(img_res.content))
                        img.verify()
                        
                        img_stream = io.BytesIO(img_res.content)
                        img_stream.seek(0)
                        return img_stream
                except:
                    continue
    except Exception as e:
        print(f"Errore durante la ricerca immagine: {e}")
    return None

def generate_news_card(title):
    """Crea una copertina stilizzata se la ricerca immagini non restituisce risultati."""
    img = Image.new("RGB", (800, 450), color="#1a1a1a")
    d = ImageDraw.Draw(img)
    
    # Bordi stilizzati arancione/rosso
    d.rectangle([(15, 15), (785, 435)], outline="#E74C3C", width=4)
    d.rectangle([(25, 25), (775, 425)], outline="#F39C12", width=2)
    
    d.text((40, 40), "ONE PIECE ITALIA NEWS", fill="#F39C12")
    
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
        print("Errore: Credenziali mancanti nelle variabili d'ambiente.")
        return

    bot = Bot(token=BOT_TOKEN)
    feed = feedparser.parse(RSS_FEED)
    new_posts_counter = 0

    for entry in feed.entries[:10]:
        title = entry.title
        link = entry.link
        uid = make_id(title)

        if uid in posted:
            continue

        print(f"Elaborazione notizia: {title}")
        
        # Cerca l'immagine tramite motore di ricerca dinamico
        image_stream = get_image_from_search(title)
        
        # Fallback se non trova nulla sul web
        if not image_stream:
            print("Nessuna immagine trovata sul web. Genero copertina grafica di riserva.")
            image_stream = generate_news_card(title)

        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"

        try:
            image_stream.name = "news_image.jpg"
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message)
            print(f"Pubblicato con successo: {title}")
            
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Errore durante l'invio su Telegram: {e}")

    print(f"Fine sessione. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
