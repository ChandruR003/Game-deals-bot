import requests
import os
import json

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "sent_deals.json"
WATCH_FILE = "watchlist.json"
UPDATE_FILE = "last_update.txt"

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, data=data)


# ================= UPDATE TRACKING =================

def load_last_update():
    try:
        with open(UPDATE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0


def save_last_update(uid):
    with open(UPDATE_FILE, "w") as f:
        f.write(str(uid))


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


# ================= FILE HELPERS =================

def load_sent():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_sent(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_watchlist():
    try:
        with open(WATCH_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_watchlist(data):
    with open(WATCH_FILE, "w") as f:
        json.dump(data, f)


# ================= EPIC =================

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


# ================= STEAM =================

def get_steam_deals():

    url = "https://store.steampowered.com/api/featuredcategories?cc=IN&l=en"

    data = requests.get(url).json()

    specials = data["specials"]["items"]

    deals = []
    free_games = []

    count = 1

    for game in specials[:30]:

        name = game["name"]

        original = game["original_price"] / 100
        current = game["final_price"] / 100

        discount = game["discount_percent"]

        game_id = game["id"]

        # FREE
        if current == 0:

            free_games.append({
                "id": f"steam_free_{game_id}",
                "text": f"🆓 {name} (FREE on Steam)"
            })

        # DISCOUNT
        elif discount >= 30:

            tag = ""

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


# ================= MAIN =================

def main():

    sent = load_sent()
    watchlist = load_watchlist()

    # -------- COMMAND HANDLER --------

    updates = get_updates()

    for u in updates:

        if "message" not in u:
            continue

        text = u["message"].get("text", "").lower()

        if not text.startswith("/"):
            continue

        parts = text.split(" ", 1)

        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        # ADD
        if cmd == "/add" and arg:

            if arg not in watchlist:

                watchlist.append(arg)
                save_watchlist(watchlist)

                send_telegram(f"✅ Added: {arg}")

            else:
                send_telegram(f"⚠️ Already watching: {arg}")

        # REMOVE
        elif cmd == "/remove" and arg:

            if arg in watchlist:

                watchlist.remove(arg)
                save_watchlist(watchlist)

                send_telegram(f"❌ Removed: {arg}")

            else:
                send_telegram(f"⚠️ Not found: {arg}")

        # CLEAR
        elif cmd == "/clear":

            watchlist = []
            save_watchlist(watchlist)

            send_telegram("🗑️ Watchlist cleared")

        # LIST
        elif cmd == "/list":

            if watchlist:

                send_telegram(
                    "📌 Your Watchlist:\n" +
                    "\n".join(watchlist)
                )

            else:
                send_telegram("📭 Watchlist empty")


    # -------- DEAL CHECK --------

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

        name_lower = text.lower()

        # WATCH ALERT
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
        return


    # -------- MESSAGE --------

    message = "🎮 Game Deals Update\n\n"


    message += "🟦 Epic Free:\n"
    message += "\n".join(new_free) if new_free else "No free games."
    message += "\n\n"


    message += "🟦 Epic Discounts:\n"
    message += "\n".join(new_epic) if new_epic else "No discounts."
    message += "\n\n"


    message += "🟩 Steam Free:\n"
    message += "\n".join(new_steam_free) if new_steam_free else "No free games."
    message += "\n\n"


    message += "🟩 Steam Deals:\n"
    message += "\n".join(new_steam) if new_steam else "No deals."


    send_telegram(message)

    save_sent(new_sent)
    save_watchlist(watchlist)


# ================= RUN =================

if __name__ == "__main__":
    main()
