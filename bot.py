import requests
from bs4 import BeautifulSoup
import telegram
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=BOT_TOKEN)

articles = [
    "https://www.animeclick.it",
    "https://anime.everyeye.it",
    "https://www.onepiece.it"
]

posted = 0

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

            image = None

            img = soup.find("img")

            if img:
                image = img.get("src")

            message = f"🔥 {title}\n\n📰 {href}\n\n#onepiece"

            try:

                if image:
                    bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=image,
                        caption=message
                    )
                else:
                    bot.send_message(
                        chat_id=CHAT_ID,
                        text=message
                    )

                print("Pubblicato:", title)

                posted += 1

                time.sleep(15)

                if posted >= 30:
                    break

            except Exception as e:
                print(e)

        if posted >= 30:
            break

    except Exception as e:
        print(e)
