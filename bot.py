import requests
import os
import json
import datetime
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "sent_deals.json"
WATCH_FILE = "watchlist.json"
PRICE_FILE = "price_history.json"
UPDATE_FILE = "last_update.txt"
DAILY_FILE = "last_daily.txt"


# ---------------- TELEGRAM ----------------

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)


def load_last_update():
    try:
        with open(UPDATE_FILE, "r") as f:
            return int(f.read())
    except:
        return 0


def save_last_update(val):
    with open(UPDATE_FILE, "w") as f:
        f.write(str(val))


def get_updates():

    last_id = load_last_update()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last_id + 1}

    r = requests.get(url, params=params).json()

    if not r.get("result"):
        return []

    updates = r["result"]

    save_last_update(updates[-1]["update_id"])

    return updates


# ---------------- STORAGE ----------------

def load_file(name, default):
    try:
        with open(name, "r") as f:
            return json.load(f)
    except:
        return default


def save_file(name, data):
    with open(name, "w") as f:
        json.dump(data, f)


def load_daily():
    try:
        with open(DAILY_FILE, "r") as f:
            return f.read().strip()
    except:
        return ""


def save_daily(val):
    with open(DAILY_FILE, "w") as f:
        f.write(val)


# ---------------- EPIC ----------------

def get_epic_deals():

    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US"

    data = requests.get(url).json()

    games = data["data"]["Catalog"]["searchStore"]["elements"]

    free = []
    discount = []

    for g in games:

        title = g["title"]
        price = g["price"]["totalPrice"]

        orig = price["originalPrice"] / 100
        now = price["discountPrice"] / 100
        off = price["discount"]

        if now == 0:
            free.append(f"🆓 {title}")

        elif off > 0:
            discount.append(
                f"💰 {title}\nWas: ₹{orig}\nNow: ₹{now} ({off}% OFF)"
            )

    return free, discount


# ---------------- STEAM ----------------

def get_steam_deals():

    url = "https://store.steampowered.com/api/featuredcategories?cc=IN&l=en"

    data = requests.get(url).json()

    items = data["specials"]["items"]

    deals = []
    free = []

    count = 1

    for g in items[:30]:

        name = g["name"]
        orig = g["original_price"] / 100
        now = g["final_price"] / 100
        off = g["discount_percent"]
        gid = str(g["id"])

        if now == 0:

            free.append(f"🆓 {name}")

        elif off >= 30:

            tag = " 🔥" if off >= 80 else ""

            deals.append(
                f"{count}. {name}{tag}\nWas: ₹{orig}\nNow: ₹{now} ({off}% OFF)"
            )

            count += 1

    return deals, free


# ---------------- SUMMARY ----------------

def build_summary():

    epic_free, epic_disc = get_epic_deals()
    steam_deals, steam_free = get_steam_deals()

    msg = "🎮 Game Deals Summary\n\n"

    msg += "🟦 Epic Free:\n"
    msg += "\n".join(epic_free) if epic_free else "None"
    msg += "\n\n"

    msg += "🟦 Epic Discounts:\n"
    msg += "\n".join(epic_disc) if epic_disc else "None"
    msg += "\n\n"

    msg += "🟩 Steam Free:\n"
    msg += "\n".join(steam_free) if steam_free else "None"
    msg += "\n\n"

    msg += "🟩 Steam Deals (30%+):\n"
    msg += "\n".join(steam_deals) if steam_deals else "None"

    return msg


# ---------------- DAILY ----------------

def check_daily():

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

    today = now.strftime("%Y-%m-%d")
    hour = now.hour

    last = load_daily()

    if hour == 21 and last != today:

        msg = "📅 Daily Deals Summary\n\n" + build_summary()

        send_telegram(msg)

        save_daily(today)


# ---------------- MAIN ----------------

def main():

    sent = load_file(DATA_FILE, [])
    watch = load_file(WATCH_FILE, [])

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
                save_file(WATCH_FILE, watch)
                send_telegram(f"✅ Added: {arg}")
            else:
                send_telegram("⚠️ Already added")


        # REMOVE
        elif cmd == "/remove" and arg:

            if arg in watch:
                watch.remove(arg)
                save_file(WATCH_FILE, watch)
                send_telegram(f"❌ Removed: {arg}")
            else:
                send_telegram("⚠️ Not found")


        # LIST
        elif cmd == "/list":

            if watch:
                send_telegram("📌 Watchlist:\n" + "\n".join(watch))
            else:
                send_telegram("📭 Empty")


        # DEALS
        elif cmd == "/deals":

            send_telegram(build_summary())


        # STATUS
        elif cmd == "/status":

            send_telegram("✅ Bot is running\n⏱ Active\n💻 Server OK")


        # HELP
        elif cmd == "/help":

            send_telegram(
                "🤖 Help\n\n"
                "/add name\n"
                "/remove name\n"
                "/list\n"
                "/deals\n"
                "/status\n"
                "/help"
            )


    check_daily()


if __name__ == "__main__":
    main()
