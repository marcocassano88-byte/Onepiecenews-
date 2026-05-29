import os
import asyncio
import hashlib
import feedparser
import requests
from telegram import Bot
import io
import re
from PIL import Image, ImageDraw, ImageFont

# Configurazione credenziali
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"
HISTORY_FILE = "posted_urls.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3"
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def clean_title_for_search(title):
    """Rimuove la testata giornalistica dal titolo."""
    cleaned = re.sub(r'\s*-\s*[^-\n]+$', '', title)
    return cleaned.strip()

def get_image_from_search(title):
    """Cerca immagini usando l'endpoint HTML di DuckDuckGo, più stabile."""
    try:
        search_term = clean_title_for_search(title)
        print(f"Cerco immagine web per: '{search_term}'")
        
        # Uso dell'endpoint di ricerca immagini standard tramite query libera
        url = "https://html.duckduckgo.com/html/"
        params = {"q": f"{search_term} image"}
        
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            # Cerchiamo pattern di URL di immagini nei risultati o nei link esterni
            urls = re.findall(r'https?://[^"\s>]+(?:\.jpg|\.jpeg|\.png)', res.text, re.IGNORECASE)
            
            # Filtriamo i loghi e i server di Google
            valid_urls = [u for u in urls if "google" not in u.lower() and "favicon" not in u.lower()]
            
            for img_url in valid_urls[:5]:
                try:
                    img_res = requests.get(img_url, headers=HEADERS, timeout=5)
                    if img_res.status_code == 200 and len(img_res.content) > 10000:
                        img = Image.open(io.BytesIO(img_res.content))
                        img.verify()
                        
                        img_stream = io.BytesIO(img_res.content)
                        img_stream.seek(0)
                        print(f"Immagine trovata con successo: {img_url}")
                        return img_stream
                except:
                    continue
    except Exception as e:
        print(f"Errore ricerca immagine: {e}")
    return None

def generate_news_card(title):
    """Crea una copertina stilizzata di alta qualità con testo grande e leggibile."""
    # Riquadro 16:9 moderno (Sfondo grigio scuro/nero)
    img = Image.new("RGB", (1200, 675), color="#121212")
    d = ImageDraw.Draw(img)
    
    # Bordi eleganti stile One Piece (Arancione/Oro)
    d.rectangle([(20, 20), (1180, 655)], outline="#E74C3C", width=6)
    d.rectangle([(32, 32), (1168, 643)], outline="#F39C12", width=3)
    
    # Intestazione protetta
    d.rectangle([(50, 50), (400, 90)], fill="#E74C3C")
    d.text((70, 60), "ONE PIECE NEWS", fill="#FFFFFF")
    
    # Puliamo il titolo per la grafica interna
    clean_title = clean_title_for_search(title)
    
    # Algoritmo di text-wrap dinamico (visto che i font di default variano su Linux/GitHub)
    words = clean_title.split()
    lines = []
    current_line = []
    
    for word in words:
        # Stimiamo la larghezza della linea basandoci sulla lunghezza dei caratteri
        test_line = " ".join(current_line + [word])
        if len(test_line) * 22 > 1000:  # Calibrato per una larghezza di ~1000px
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    lines.append(" ".join(current_line))
    
    # Calcolo della posizione Y iniziale per centrare il blocco di testo verticalmente
    total_lines = len(lines[:4])
    y_text = 337 - (total_lines * 35) 
    
    # Scrittura delle linee di testo con una dimensione simulata visivamente grande
    for line in lines[:4]:
        # Disegniamo un leggero effetto ombra per massima leggibilità
        d.text((82, y_text + 2), line, fill="#000000")
        d.text((80, y_text), line, fill="#F1C40F" if "one piece" in line.lower() else "#FFFFFF")
        y_text += 70 # Spaziatura interlinea ampia
        
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=90)
    img_byte_arr.seek(0)
    return img_byte_arr

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t: tags.append("#luffy")
    if "netflix" in t or "remake" in t: tags.append("#netflix")
    if "milano" in t: tags.append("#onepiecemilano")
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

        if uid in posted:
            continue

        print(f"\n--- Elaborazione: {title} ---")
        
        # 1. Tenta il recupero dell'immagine reale sul web
        image_stream = get_image_from_search(title)
        
        # 2. Se fallisce, genera la nuova copertina gigante e leggibile
        if not image_stream:
            print("Nessuna immagine dal web. Genero copertina premium.")
            image_stream = generate_news_card(title)

        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"

        try:
            image_stream.name = "news.jpg"
            await bot.send_photo(chat_id=CHAT_ID, photo=image_stream, caption=message)
            print(f"Inviato con successo!")
            
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Errore invio Telegram: {e}")

    print(f"\nTask terminato. Post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
