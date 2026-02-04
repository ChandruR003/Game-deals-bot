import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_epic_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US"
    data = requests.get(url).json()

    games = []
    elements = data["data"]["Catalog"]["searchStore"]["elements"]

    for game in elements:
        promotions = game.get("promotions")
        if promotions and promotions.get("promotionalOffers"):
            for offer in promotions["promotionalOffers"]:
                for promo in offer["promotionalOffers"]:
                    if promo["discountSetting"]["discountPercentage"] == 0:
                        games.append(game["title"])

    return games

def main():
    free_games = get_epic_free_games()

    if free_games:
        message = "🎮 <b>Epic Games Free Games:</b>\n\n"
        for game in free_games:
            message += f"• {game}\n"
    else:
        message = "❌ No free games right now."

    send_telegram_message(message)

if __name__ == "__main__":
    main()
