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


# ---------- EPIC GAMES ----------

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

        if current == 0:
            free_games.append({
                "id": f"epic_{title}",
                "text": f"🆓 {title} (FREE)"
            })

        elif discount > 0:
            discount_games.append({
                "id": f"epic_{title}",
                "text":
                f"💰 {title}\n"
                f"Was: ₹{original}\n"
                f"Now: ₹{current} ({discount}% OFF)"
            })

    return free_games, discount_games


# ---------- STEAM ----------

def get_steam_deals():

    url = "https://store.steampowered.com/api/featuredcategories?cc=IN&l=en"

    data = requests.get(url).json()

    specials = data["specials"]["items"]

    deals = []
    free_games = []

    count = 1

    for game in specials[:30]:  # Top 30 deals

        name = game["name"]

        original = game["original_price"] / 100
        current = game["final_price"] / 100

        discount = game["discount_percent"]

        game_id = game["id"]

        # FREE GAME
        if current == 0:
            free_games.append({
                "id": f"steam_free_{game_id}",
                "text": f"🆓 {name} (FREE on Steam)"
            })

        # DISCOUNTED GAME
        elif discount >= 30:

            tag = ""

            # HOT DEAL (80%+)
            if discount >= 80:
                tag = " 🔥 HOT DEAL"

            deals.append({
                "id": f"steam_{game_id}",
                "text":
                f"{count}. {name}{tag}\n"
                f"   Was: ₹{original}\n"
                f"   Now: ₹{current} ({discount}% OFF)"
            })

            count += 1

    return deals, free_games


# ---------- MAIN ----------

def main():

    sent = load_sent()
    new_sent = sent.copy()

    free_games, epic_discounts = get_epic_deals()
    steam_deals, steam_free = get_steam_deals()

    new_free = []
    new_epic = []
    new_steam = []
    new_steam_free = []

    for g in free_games:
        if g["id"] not in sent:
            new_free.append(g["text"])
            new_sent.append(g["id"])

    for g in epic_discounts:
        if g["id"] not in sent:
            new_epic.append(g["text"])
            new_sent.append(g["id"])

    for g in steam_deals:
        if g["id"] not in sent:
            new_steam.append(g["text"])
            new_sent.append(g["id"])

    for g in steam_free:
        if g["id"] not in sent:
            new_steam_free.append(g["text"])
            new_sent.append(g["id"])

    if not (new_free or new_epic or new_steam):
        print("No new deals")
        return

    message = "🎮 Game Deals Update\n\n"

    # Epic Free
    message += "🟦 Epic Free Games:\n"
    if new_free:
        message += "\n".join(new_free)
    else:
        message += "No new free games."

    message += "\n\n"

    # Epic Discounts
    message += "🟦 Epic Discounts:\n"
    if new_epic:
        message += "\n".join(new_epic)
    else:
        message += "No new discounts."

    message += "\n\n"

    # Steam Free
message += "🟩 Steam Free Games:\n"
if new_steam_free:
    message += "\n".join(new_steam_free)
else:
    message += "No new free games."

message += "\n\n"

# Steam Deals
message += "🟩 Steam Deals (30%+ OFF):\n"
if new_steam:
    message += "\n".join(new_steam)
else:
    message += "No new Steam deals."

    send_telegram(message)
    save_sent(new_sent)


if __name__ == "__main__":
    main()
