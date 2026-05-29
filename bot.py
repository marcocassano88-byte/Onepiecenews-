import os
import asyncio
import hashlib
import random
import feedparser
import requests
from telegram import Bot
import io
from PIL import Image, ImageDraw

# Configurazione credenziali da variabili d'ambiente GitHub
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEED = "https://news.google.com/rss/search?q=One+Piece+anime&hl=it&gl=IT&ceid=IT:it"

HISTORY_FILE = "posted_urls.txt"

# Wikimedia richiede un User-Agent identificativo unico per evitare blocchi
HEADERS = {
    "User-Agent": "OnePieceNewsBot/1.0 (marcocassano88@example.com) Python-Requests"
}

# Carica lo storico dei post già inviati per evitare duplicati
posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def generate_failsafe_image():
    """Genera un'immagine PNG di backup in memoria (riquadro arancione)."""
    img = Image.new("RGB", (800, 500), color="#F39C12")
    d = ImageDraw.Draw(img)
    d.rectangle([(20, 20), (780, 480)], outline="#FFFFFF", width=5)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def process_image_in_memory(raw_data):
    """Prende i dati scaricati, li pulisce e li converte in un flusso JPEG perfetto per Telegram."""
    try:
        img = Image.open(io.BytesIO(raw_data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        output.seek(0) # Riposiziona il cursore all'inizio del file in memoria
        return output
    except Exception as e:
        print(f"Impossibile elaborare l'immagine in memoria: {e}")
        return None

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()

characters_map = {
    "luffy": "Monkey D. Luffy", "zoro": "Roronoa Zoro", "nami": "Nami (One Piece)",
    "usopp": "Usopp", "sanji": "Sanji", "chopper": "Tony Tony Chopper",
    "robin": "Nico Robin", "franky": "Franky", "brook": "Brook", "jimbei": "Jinbe",
    "shanks": "Shanks (One Piece)", "buggy": "Buggy (One Piece)", "mihawk": "Dracule Mihawk",
    "law": "Trafalgar Law", "kid": "Eustass Kid", "sabo": "Sabo (One Piece)",
    "ace": "Portgas D. Ace", "whitebeard": "Edward Newgate", "kaido": "Kaido",
    "big mom": "Charlotte Linlin", "roger": "Gol D. Roger", "dragon": "Monkey D. Dragon",
    "garp": "Monkey D. Garp", "akainu": "Sakazuki", "aokiji": "Kuzan", "kizaru": "Borsalino",
    "imu": "Imu (One Piece)", "doflamingo": "Donquixote Doflamingo", "crocodile": "Crocodile (One Piece)",
    "enel": "Enel (One Piece)", "lucci": "Rob Lucci", "kuma": "Bartholomew Kuma",
    "bonney": "Jewelry Bonney", "yamato": "Yamato (One Piece)", "momonosuke": "Momonosuke",
    "kinemon": "Kin'emon", "moria": "Gecko Moria", "hancock": "Boa Hancock",
    "ivankov": "Emporio Ivankov", "rocks": "Rocks D. Xebec", "gear 5": "Monkey D. Luffy",
    "joy boy": "Joy Boy", "nika": "Nika (One Piece)"
}

def get_wiki_image_url(category_name):
    """Recupera l'URL dell'immagine da Wikimedia."""
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "list": "categorymembers",
            "cmtitle": "Category:" + category_name, "cmtype": "file", "cmlimit": 30
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        files = r.json().get("query", {}).get("categorymembers", [])
        if not files: return None

        valid_files = [f for f in files if f["title"].lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not valid_files: valid_files = files

        random_file = random.choice(valid_files)["title"]
        
        params2 = {
            "action": "query", "format": "json", "titles": random_file,
            "prop": "imageinfo", "iiprop": "url"
        }
        r2 = requests.get(url, params=params2, headers=HEADERS, timeout=10)
        pages = r2.json().get("query", {}).get("pages", {})
        for p in pages.values():
            if "imageinfo" in p:
                return p["imageinfo"][0]["url"]
    except:
        pass
    return None

def download_image_stream(title):
    """Cerca l'immagine adatta e restituisce il flusso di byte pronto, senza salvare su disco."""
    t = title.lower()
    
    # 1. Cerca per personaggio specifico
    for key, category in characters_map.items():
        if key in t:
            img_url = get_wiki_image_url(category)
            if img_url:
                try:
                    raw_data = requests.get(img_url, headers=HEADERS, timeout=10).content
                    stream = process_image_in_memory(raw_data)
                    if stream: return stream
                except: pass

    # 2. Cerca nella categoria generale One Piece
    img_url = get_wiki_image_url("One Piece")
    if img_url:
        try:
            raw_data = requests.get(img_url, headers=HEADERS, timeout=10).content
            stream = process_image_in_memory(raw_data)
            if stream: return stream
        except: pass

    return None

def hashtags(title):
    t = title.lower()
    tags = ["#onepiece", "#anime", "#manga"]
    if "luffy" in t: tags.append("#luffy")
    if "zoro" in t: tags.append("#zoro")
    if "shanks" in t: tags.append("#shanks")
    if "gear 5" in t: tags.append("#gear5")
    if "imu" in t: tags.append("#imu")
    return " ".join(tags)

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: BOT_TOKEN o CHAT_ID mancano.")
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

        print(f"--- Elaborazione post: {title} ---")
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"
        
        # Ottieni l'immagine direttamente come flusso di memoria (BytesIO)
        photo_stream = download_image_stream(title)

        try:
            if photo_stream:
                print("Invio immagine reale da memoria...")
                photo_stream.name = "image.jpg" # Telegram ha bisogno di un nome fittizio per capire l'estensione
                await bot.send_photo(chat_id=CHAT_ID, photo=photo_stream, caption=message)
            else:
                print("Immagine reale fallita. Invio riquadro di backup...")
                failsafe = generate_failsafe_image()
                failsafe.name = "backup.png"
                await bot.send_photo(chat_id=CHAT_ID, photo=failsafe, caption=message)
            
            print(f"Pubblicato con successo!")
            
            # Salva nello storico
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5) # Pausa anti-flood per Telegram

        except Exception as e:
            print(f"Errore critico durante l'invio su Telegram: {e}")

    print(f"Task terminato. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
