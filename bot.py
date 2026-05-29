import requests
from bs4 import BeautifulSoup
import telegram
import os
import time
import random

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=BOT_TOKEN)

articles = [
    "https://www.animeclick.it",
    "https://anime.everyeye.it",
    "https://www.onepiece.it"
]

posted_titles = set()

for site in articles:

    try:
        r = requests.get(site, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.find_all("a")

        for link in links:

            href = link.get("href")
            title = link.get_text(strip=True)

            if not href:
                continue

            if "one piece" not in title.lower():
                continue

            if len(title) < 20:
                continue

            if title in posted_titles:
                continue

            posted_titles.add(title)

            if not href.startswith("http"):
                continue

            message = f"""
🔥 ONE PIECE NEWS

{title}

📰 Leggi qui:
{href}

#onepiece #anime #luffy
"""

            try:

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=message
                )

                print("Pubblicato:", title)

                # pausa lunga anti flood
                time.sleep(random.randint(40, 70))

            except Exception as e:
                print(e)

    except Exception as e:
        print(e)
