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

CACHE_DIR = "cache"
HISTORY_FILE = "posted_urls.txt"
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "OnePieceNewsBot/1.0 (marcocassano88@example.com) Python-Requests"
}

posted = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        posted = set(line.strip() for line in f if line.strip())

def generate_failsafe_image():
    """Genera un'immagine PNG valida di backup se non ci sono immagini reali disponibili."""
    img = Image.new("RGB", (800, 500), color="#F39C12")
    d = ImageDraw.Draw(img)
    d.rectangle([(20, 20), (780, 480)], outline="#FFFFFF", width=5)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def optimize_and_verify_image(raw_data, output_path):
    """Verifica che l'immagine sia valida e la forza in formato JPEG standard per Telegram."""
    try:
        img = Image.open(io.BytesIO(raw_data))
        # Se l'immagine è in modalità RGBA (trasparente) o P, la converte in RGB per il formato JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Salva l'immagine standardizzandola al massimo
        img.save(output_path, format="JPEG", quality=85)
        return True
    except Exception as e:
        print(f"File scaricato non valido o non convertibile: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

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

def get_wiki_image(category_name):
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "list": "categorymembers",
            "cmtitle": "Category:" + category_name, "cmtype": "file", "cmlimit": 50
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        
        files = r.json().get("query", {}).get("categorymembers", [])
        if not files: return None

        # Filtra i file tenendo solo estensioni standard accettate da Telegram ed evita gli .svg
        valid_files = [f for f in files if f["title"].lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not valid_files: 
            valid_files = files # fallback se la categoria ha solo nomi strani

        random_file = random.choice(valid_files)["title"]
        
        params2 = {
            "action": "query", "format": "json", "titles": random_file,
            "prop": "imageinfo", "iiprop": "url"
        }
        r2 = requests.get(url, params=params2, headers=HEADERS, timeout=10)
        if r2.status_code != 200: return None
        
        pages = r2.json().get("query", {}).get("pages", {})
        for p in pages.values():
            if "imageinfo" in p:
                return p["imageinfo"][0]["url"]
    except Exception as e:
        print(f"Errore API Wikimedia per {category_name}: {e}")
    return None

def get_character_image(title):
    t = title.lower()
    for key, category in characters_map.items():
        if key in t:
            cache_path = os.path.join(CACHE_DIR, f"{key}.jpg")
            if os.path.exists(cache_path): return cache_path
            
            img_url = get_wiki_image(category)
            if img_url:
                try:
                    img_data = requests.get(img_url, headers=HEADERS, timeout=10).content
                    # Converte e salva solo se l'immagine è sana ed è un vero JPG/PNG
                    if optimize_and_verify_image(img_data, cache_path):
                        return cache_path
                except:
                    pass

    cache_path = os.path.join(CACHE_DIR, "default.jpg")
    if os.path.exists(cache_path): return cache_path
    
    img_url = get_wiki_image("One Piece")
    if img_url:
        try:
            img_data = requests.get(img_url, headers=HEADERS, timeout=10).content
            if optimize_and_verify_image(img_data, cache_path):
                return cache_path
        except:
            pass
            
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
        print("Errore: BOT_TOKEN o CHAT_ID non configurati nelle variabili d'ambiente.")
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

        image_path = get_character_image(title)
        message = f"🔥 {title}\n\n👉 Fonte: {link}\n\n{hashtags(title)}"

        try:
            if image_path and os.path.exists(image_path):
                print(f"Utilizzo immagine reale convertita: {image_path}")
                with open(image_path, "rb") as photo_file:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo_file, caption=message)
            else:
                print(f"Immagine reale non disponibile. Attivazione backup per: {title}")
                failsafe_file = generate_failsafe_image()
                failsafe_file.name = "news_default.png"
                await bot.send_photo(chat_id=CHAT_ID, photo=failsafe_file, caption=message)
            
            print(f"Pubblicato con successo: {title}")
            
            posted.add(uid)
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"{uid}\n")
                
            new_posts_counter += 1
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Errore Telegram durante l'invio di '{title}': {e}")

    print(f"Task terminato. Nuovi post pubblicati: {new_posts_counter}")

if __name__ == "__main__":
    asyncio.run(main())
