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

    free_games = []
    discount_games = []

    for game in games:

        title = game["title"]
        price = game["price"]["totalPrice"]

        original = price["originalPrice"] / 100
        current = price["discountPrice"] / 100

        discount = price["discount"]

        # Free games
        if current == 0:
            free_games.append({
                "id": title,
                "text": f"🆓 {title} (FREE)"
            })

        # Discounted games
        elif discount > 0:
            discount_games.append({
                "id": title,
                "text":
                f"💰 {title}\n"
                f"Was: ${original}\n"
                f"Now: ${current} ({discount}% OFF)"
            })

    return free_games, discount_games


def main():

    sent = load_sent()
    new_sent = sent.copy()

    free_games, discount_games = get_epic_deals()

    free_msgs = []
    discount_msgs = []

    # New free games
    for game in free_games:
        if game["id"] not in sent:
            free_msgs.append(game["text"])
            new_sent.append(game["id"])

    # New discount games
    for game in discount_games:
        if game["id"] not in sent:
            discount_msgs.append(game["text"])
            new_sent.append(game["id"])

    # Build message
    message = "🎮 Epic Games Store Update\n\n"

    # Free section
    if free_msgs:
        message += "🆓 Free Games:\n"
        message += "\n".join(free_msgs)
    else:
        message += "🆓 Free Games:\nNo new free games right now."

    message += "\n\n"

    # Discount section
    if discount_msgs:
        message += "💰 Discount Offers:\n"
        message += "\n".join(discount_msgs)
    else:
        message += "💰 Discount Offers:\nNo discount offers right now."

    # Send only if something is new
    if free_msgs or discount_msgs:
        send_telegram(message)
        save_sent(new_sent)
    else:
        print("No new updates")


if __name__ == "__main__":
    main()
