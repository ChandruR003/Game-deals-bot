import requests
import os
import json
import datetime

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCH_FILE = "watchlist.json"
DAILY_FILE = "last_daily.txt"
UPDATE_FILE = "last_update.txt"


# ---------------- TELEGRAM ----------------

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)


def send_photo(text, img):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": CHAT_ID,
        "caption": text,
        "photo": img
    }
    requests.post(url, data=data)


# ---------------- STORAGE ----------------

def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)


def load_text(file):
    try:
        return open(file).read().strip()
    except:
        return ""


def save_text(file, val):
    with open(file, "w") as f:
        f.write(val)


# ---------------- UPDATES ----------------

def load_last_update():
    try:
        return int(open(UPDATE_FILE).read())
    except:
        return 0


def save_last_update(val):
    open(UPDATE_FILE, "w").write(str(val))


def get_updates():

    last = load_last_update()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last + 1}

    r = requests.get(url, params=params).json()

    if not r.get("result"):
        return []

    updates = r["result"]

    save_last_update(updates[-1]["update_id"])

    return updates


# ---------------- EPIC ----------------

def get_epic():

    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US"

    data = requests.get(url).json()

    games = data["data"]["Catalog"]["searchStore"]["elements"]

    free = []
    deals = []

    for g in games:

        title = g["title"]
        price = g["price"]["totalPrice"]

        orig = price["originalPrice"] / 100
        now = price["discountPrice"] / 100
        off = price["discount"]

        img = g["keyImages"][0]["url"] if g.get("keyImages") else None

        if now == 0:
            free.append((title, img))

        elif off >= 30:
            deals.append((title, orig, now, off, img))

    return free, deals


# ---------------- STEAM ----------------

def get_steam():

    url = "https://store.steampowered.com/api/featuredcategories?cc=IN&l=en"

    data = requests.get(url).json()

    items = data["specials"]["items"]

    free = []
    deals = []

    for g in items:

        name = g["name"]

        orig = g["original_price"] / 100
        now = g["final_price"] / 100
        off = g["discount_percent"]

        img = g.get("header_image")

        if now == 0:
            free.append((name, img))

        elif off >= 30:
            deals.append((name, orig, now, off, img))

    return free, deals


# ---------------- DEALS (IMAGES) ----------------

def send_deals():

    epic_free, epic_deals = get_epic()
    steam_free, steam_deals = get_steam()

    send_message("🎮 Top Game Deals\n")

    # Epic Free
    for g in epic_free[:3]:
        send_photo(f"🆓 Epic: {g[0]}", g[1])

    # Epic Hot
    for g in epic_deals[:3]:
        send_photo(
            f"💰 Epic: {g[0]}\n₹{g[1]} → ₹{g[2]} ({g[3]}% OFF)",
            g[4]
        )

    # Steam Free
    for g in steam_free[:3]:
        send_photo(f"🆓 Steam: {g[0]}", g[1])

    # Steam Hot
    for g in steam_deals[:3]:
        send_photo(
            f"💰 Steam: {g[0]}\n₹{g[1]} → ₹{g[2]} ({g[3]}% OFF)",
            g[4]
        )


# ---------------- DETAILS (TEXT) ----------------

def send_details():

    epic_free, epic_deals = get_epic()
    steam_free, steam_deals = get_steam()

    msg = "📋 Full Deals List\n\n"

    msg += "🟦 Epic\n"

    for g in epic_free:
        msg += f"🆓 {g[0]}\n"

    for g in epic_deals:
        msg += f"💰 {g[0]} ₹{g[1]}→₹{g[2]} ({g[3]}%)\n"

    msg += "\n🟩 Steam\n"

    for g in steam_free:
        msg += f"🆓 {g[0]}\n"

    for g in steam_deals:
        msg += f"💰 {g[0]} ₹{g[1]}→₹{g[2]} ({g[3]}%)\n"

    send_message(msg)


# ---------------- DAILY ----------------

def daily_check():

    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)

    today = now.strftime("%Y-%m-%d")

    hour = now.hour

    last = load_text(DAILY_FILE)

    if hour == 21 and last != today:

        send_message("📅 Daily Summary\n")

        send_deals()

        save_text(DAILY_FILE, today)


# ---------------- MAIN ----------------

def main():

    watch = load_json(WATCH_FILE, [])

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

            if arg not in watch:

                watch.append(arg)

                save_json(WATCH_FILE, watch)

                send_message("✅ Added")

            else:
                send_message("⚠️ Already added")


        # REMOVE
        elif cmd == "/remove" and arg:

            if arg in watch:

                watch.remove(arg)

                save_json(WATCH_FILE, watch)

                send_message("❌ Removed")

            else:
                send_message("⚠️ Not found")


        # LIST
        elif cmd == "/list":

            if watch:

                send_message("📌 Wishlist:\n" + "\n".join(watch))

            else:
                send_message("📭 Empty")


        # DEALS
        elif cmd == "/deals":

            send_deals()


        # DETAILS
        elif cmd == "/details":

            send_details()


        # HELP
        elif cmd == "/help":

            send_message(
                "/deals → Top games\n"
                "/details → Full list\n"
                "/add name\n"
                "/remove name\n"
                "/list\n"
            )


    daily_check()


if __name__ == "__main__":
    main()
