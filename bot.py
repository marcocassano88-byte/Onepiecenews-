import os
import asyncio
import hashlib
import requests
from telegram import Bot
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ACCOUNTS = [
    "OP_Spoiler_IT",   
    "OnePiece_It",     
    "BikeAndRaft",     
    "OPLiveActionIT"   
]

HISTORY_FILE = "posted_tweets.txt"

def make_id(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

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

    for account in ACCOUNTS:
        print(f"\n--- SCRAPING DIRETTO DA X: @{account} ---")
        
        # Interroghiamo direttamente l'estensione di rete globale di X senza passare da Nitter
        api_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(api_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"X ha risposto con errore {response.status_code} per @{account}")
                continue
                
            # X risponde con i dati strutturati della timeline nascosti nell'HTML della pagina ufficiale
            html_content = response.text
            data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html_content)
            
            tweets = []
            if data_match:
                json_data = json.loads(data_match.group(1))
                entries = json_data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries", [])
                for e in entries:
                    if "tweet" in e: tweets.append(e["tweet"])
            else:
                # Metodo di riserva se la struttura è quella pulita dei widget
                import json
                try:
                    data_match_alt = re.search(r'props":(\{.*?\})\}\}', html_content)
                    if data_match_alt:
                        json_data = json.loads(data_match_alt.group(1) + "}}")
                        tweets = json_data.get("timeline", {}).get("entries", [])
                except:
                    pass

            if not tweets:
                # Estrazione bruta via Regex se JSON fallisce (indistruttibile)
                raw_tweets = re.findall(r'"text"\s*:\s*"(.*?)"', html_content)
                raw_images = re.findall(r'"media_url_https"\s*:\s*"(.*?)"', html_content)
                print(f"Trovati {len(raw_tweets)} elementi grezzi. Elaborazione di massa...")
                
                # Ricostruzione d'emergenza
                for idx, txt in enumerate(raw_tweets[:12]):
                    try:
                        clean_text = txt.encode().decode('unicode-escape')
                        clean_text = re.sub(r'https?://[^\s]+', '', clean_text).strip()
                        if len(clean_text) < 15: continue
                        
                        uid = make_id(clean_text)
                        if uid in posted_ids: continue
                        
                        img = raw_images[idx] if idx < len(raw_images) else None
                        if img: img = img.replace("\\", "")
                        
                        tweets.append({"text": clean_text, "media": img, "fallback": True})
                    except:
                        continue

            # Avvio invio reale su Telegram
            for tw in tweets[:15]:
                is_fallback = isinstance(tw, dict) and "fallback" in tw
                
                if is_fallback:
                    tweet_text = tw["text"]
                    img_url = tw["media"]
                else:
                    tweet_text = tw.get("text", "")
                    img_url = None
                    media = tw.get("extended_entities", {}).get("media", [])
                    if media:
                        img_url = media[0].get("media_url_https")

                if not tweet_text: continue
                uid = make_id(tweet_text)
                if uid in posted_ids: continue

                # Formattazione corretta
                lines = tweet_text.split('\n')
                title_line = lines[0]
                remaining_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

                message = f"📢 <b>{title_line}</b>\n"
                if remaining_text:
                    message += f"\n{remaining_text}\n"
                message += f"\n👉 <a href='https://x.com/{account}'>Apri il post originale su X</a>\n\n#{account.lower()} #onepiece"

                try:
                    if img_url and img_url.startswith("http"):
                        # Invia l'immagine ORIGINALE scaricata direttamente dai server di X
                        await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=message, parse_mode="HTML")
                        print(" -> [OK] Post inviato con immagine reale di X!")
                    else:
                        # Se è un post di testo, lo manda pulito senza immagini a caso inventate da me
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
                        print(" -> [OK] Post di testo inviato!")

                    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{uid}\n")
                    posted_ids.add(uid)
                    total_uploaded += 1
                    await asyncio.sleep(6)
                    
                except Exception as e:
                    print(f"Errore invio: {e}")

        except Exception as e:
            print(f"Errore generale per {account}: {e}")
            continue

    print(f"\nFatto! Caricati sul canale: {total_uploaded} post reali.")

if __name__ == "__main__":
    import json
    asyncio.run(main())
