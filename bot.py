import requests
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "sent_deals.json"
UPDATE_FILE = "last_update.txt"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)

def get_updates():

    last_id = load_last_update()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {
        "offset": last_id + 1,
        "timeout": 10
    }

    r = requests.get(url, params=params).json()

    if not r.get("result"):
        return []

    updates = r["result"]

    newest = updates[-1]["update_id"]
    save_last_update(newest)

    return updates


def load_sent():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_sent(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_last_update():
    try:
        with open("last_update.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_last_update(uid):
    with open("last_update.txt", "w") as f:
        f.write(str(uid))

# ---------- PRICE HISTORY ----------

PRICE_FILE = "price_history.json"


def load_prices():
    try:
        with open(PRICE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_prices(data):
    with open(PRICE_FILE, "w") as f:
        json.dump(data, f)

# ---------- WATCHLIST ----------

WATCH_FILE = "watchlist.json"


def load_watchlist():
    try:
        with open(WATCH_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_watchlist(data):
    with open(WATCH_FILE, "w") as f:
        json.dump(data, f)

# ---------- UPDATE TRACKER ----------

UPDATE_FILE = "last_update.txt"


def load_last_update():
    try:
        with open(UPDATE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0


def save_last_update(val):
    with open(UPDATE_FILE, "w") as f:
        f.write(str(val))



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
    prices = load_prices()
    watchlist = load_watchlist()

    updates = get_updates()

    for u in updates:

        if "message" not in u:
            continue

        text = u["message"].get("text", "")
        chat = u["message"]["chat"]["id"]

        if not text.startswith("/"):
            continue

        parts = text.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1].lower() if len(parts) > 1 else ""

        # ADD
        if cmd == "/add" and arg:

            if arg not in watchlist:
                watchlist.append(arg)
                save_watchlist(watchlist)

                send_telegram(f"✅ Added to watchlist: {arg}")

            else:
                send_telegram(f"⚠️ Already watching: {arg}")

        # REMOVE
        elif cmd == "/remove" and arg:

            if arg in watchlist:
                watchlist.remove(arg)
                save_watchlist(watchlist)

                send_telegram(f"❌ Removed: {arg}")

            else:
                send_telegram(f"⚠️ Not in list: {arg}")

        # LIST
        elif cmd == "/list":

            if watchlist:
                send_telegram(
                    "📌 Your Watchlist:\n" +
                    "\n".join(watchlist)
                )
            else:
                send_telegram("📭 Watchlist is empty")

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

        game_id = g["id"]
        text = g["text"]

        # Extract price from text
        lines = text.split("\n")
        now_line = lines[2]  # "Now: ₹xxx (xx% OFF)"
        now_price = float(now_line.split("₹")[1].split(" ")[0])

        # Get lowest price
        if game_id in prices:
            lowest = min(prices[game_id], now_price)
            prices[game_id].append(now_price)
        else:
            lowest = now_price
            prices[game_id] = [now_price]

        
# Add lowest price info
        text += f"\n   Lowest: ₹{lowest}"

        # WATCHLIST ALERT
        name_lower = text.lower()

        for w in watchlist:
            if w in name_lower:
                send_telegram(f"🔔 WATCH ALERT!\n{text}")

        if game_id not in sent:
            new_steam.append(text)
            new_sent.append(game_id)


    for g in steam_free:
        if g["id"] not in sent:
            new_steam_free.append(g["text"])
            new_sent.append(g["id"])

    if not (new_free or new_epic or new_steam or new_steam_free):
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
    save_prices(prices)
    save_watchlist(watchlist)

if __name__ == "__main__":
    main()
