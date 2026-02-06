import requests
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "sent_deals.json"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)


def load_sent():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_sent(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def get_epic_deals():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US"
    data = requests.get(url).json()

    games = data["data"]["Catalog"]["searchStore"]["elements"]

    deals = []

    for game in games:

        title = game["title"]
        price = game["price"]["totalPrice"]

        original = price["originalPrice"] / 100
        current = price["discountPrice"] / 100

        discount = price["discount"]

        # Free game
        if current == 0:
            deals.append({
                "id": title,
                "text": f"🆓 {title} (FREE)"
            })

        # Discounted game
        elif discount > 0:
            percent = discount

            deals.append({
                "id": title,
                "text":
                f"💰 {title}\n"
                f"Was: ${original}\n"
                f"Now: ${current} ({percent}% OFF)"
            })

    return deals


def main():

    sent = load_sent()
    new_sent = sent.copy()

    deals = get_epic_deals()

    new_messages = []

    for deal in deals:
        if deal["id"] not in sent:
            new_messages.append(deal["text"])
            new_sent.append(deal["id"])

    if new_messages:

        msg = "🎮 New Epic Deals\n\n"
        msg += "\n\n".join(new_messages)

        send_telegram(msg)
        save_sent(new_sent)

    else:
        print("No new deals")


if __name__ == "__main__":
    main()
