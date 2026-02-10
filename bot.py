import requests
import os
import json
import datetime


# ================= CONFIG ================= #

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCH_FILE = "watchlist.json"
DAILY_FILE = "last_daily.txt"
UPDATE_FILE = "last_update.txt"


# ================= TELEGRAM ================= #

def send_message(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, data=data)


def send_photo(text, image):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {
        "chat_id": CHAT_ID,
        "caption": text,
        "photo": image,
        "parse_mode": "HTML"
    }

    requests.post(url, data=data)


def send_menu():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": "🎮 <b>Game Deals Menu</b>",
        "parse_mode": "HTML",
        "reply_markup": json.dumps({
            "keyboard": [
                ["🔥 Deals", "📜 Details"],
                ["🟦 Epic", "🟩 Steam"],
                ["📌 Wishlist", "❓ Help"],
                ["🌐 Epic Store", "🌐 Steam Store"]
            ],
            "resize_keyboard": True,
            "persistent": True
        })
    }

    requests.post(url, data=data)


# ================= STORAGE ================= #

def load_file(name, default):
    try:
        with open(name) as f:
            return json.load(f)
    except:
        return default


def save_file(name, data):
    with open(name, "w") as f:
        json.dump(data, f)


def load_update():
    try:
        with open(UPDATE_FILE) as f:
            return int(f.read())
    except:
        return 0


def save_update(val):
    with open(UPDATE_FILE, "w") as f:
        f.write(str(val))


def load_daily():
    try:
        with open(DAILY_FILE) as f:
            return f.read()
    except:
        return ""


def save_daily(val):
    with open(DAILY_FILE, "w") as f:
        f.write(val)


# ================= TELEGRAM UPDATES ================= #

def get_updates():

    last = load_update()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last + 1}

    data = requests.get(url, params=params).json()

    if not data.get("result"):
        return []

    updates = data["result"]

    save_update(updates[-1]["update_id"])

    return updates


# ================= EPIC ================= #

def get_epic():

    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

    data = requests.get(url).json()

    games = data["data"]["Catalog"]["searchStore"]["elements"]

    free = []
    deals = []

    for g in games:

        title = g["title"]

        price = g["price"]["totalPrice"]

        orig = price["originalPrice"] / 100
        now = price["discountPrice"] / 100

        off = int(price["discount"])

        end = "Unknown"

        promos = g.get("promotions")

        if promos and promos.get("promotionalOffers"):
            p = promos["promotionalOffers"]
            if p and p[0].get("promotionalOffers"):
                end = p[0]["promotionalOffers"][0]["endDate"][:10]

        image = None

        if g.get("keyImages"):
            image = g["keyImages"][0]["url"]

        if now == 0:

            free.append({
                "name": title,
                "img": None,
                "end": end
            })

        elif off >= 30:

            deals.append({
                "name": title,
                "orig": orig,
                "now": now,
                "off": off,
                "img": image,
                "end": end
            })

    return free[:5], deals[:5], free, deals


# ================= STEAM ================= #

def get_steam():

    url = "https://store.steampowered.com/api/featuredcategories?cc=IN"

    data = requests.get(url).json()

    items = data["specials"]["items"]

    free = []
    deals = []

    for g in items:

        name = g["name"]

        orig = g["original_price"] / 100
        now = g["final_price"] / 100

        off = g["discount_percent"]

        img = g["header_image"]

        if now == 0:

            free.append({
                "name": name,
                "img": None
            })

        elif off >= 30:

            deals.append({
                "name": name,
                "orig": orig,
                "now": now,
                "off": off,
                "img": img
            })

    return free[:5], deals[:5], free, deals


# ================= DEALS ================= #

def send_deals():

    _, e_hot, _, _ = get_epic()
    _, s_hot, _, _ = get_steam()

    send_message("🎮 <b>Game Deals</b>")

    for g in e_hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)\n"
            f"Ends: {g['end']}"
        )

        send_photo(txt, g["img"])


    for g in s_hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)"
        )

        send_photo(txt, g["img"])


def send_epic():

    _, hot, _, _ = get_epic()

    for g in hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}%)"
        )

        send_photo(txt, g["img"])


def send_steam():

    _, hot, _, _ = get_steam()

    for g in hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}%)"
        )

        send_photo(txt, g["img"])


# ================= DETAILS ================= #

def send_details():

    _, _, e_free, e_deals = get_epic()
    _, _, s_free, s_deals = get_steam()

    msg = "📜 <b>All Deals</b>\n\n"

    msg += "🟦 Epic\n"

    i = 1

    for g in e_free:
        msg += f"{i}. 🆓 {g['name']}\n"
        i += 1

    for g in e_deals:
        msg += f"{i}. {g['name']} — ₹{g['now']} ({g['off']}%)\n"
        i += 1


    msg += "\n🟩 Steam\n"

    i = 1

    for g in s_free:
        msg += f"{i}. 🆓 {g['name']}\n"
        i += 1

    for g in s_deals:
        msg += f"{i}. {g['name']} — ₹{g['now']} ({g['off']}%)\n"
        i += 1


    send_message(msg)


# ================= DAILY ================= #

def check_daily():

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

    today = now.strftime("%Y-%m-%d")

    last = load_daily()

    if now.hour == 21 and last != today:

        send_deals()
        save_daily(today)


# ================= MAIN ================= #

def main():

    watch = load_file(WATCH_FILE, [])

    updates = get_updates()

    for u in updates:

        if "message" not in u:
            continue

        text = u["message"].get("text", "").strip().lower()

        #START COMMAND
        if text == "/start":
            send_message("👋 Welcome to Game Deals Bot!")
            send_menu()
            continue
        
        if text in ["🔥 deals", "/deals"]:
            send_deals()

        elif text in ["📜 details", "/details"]:
            send_details()

        elif text == "🟦 epic":
            send_epic()

        elif text == "🟩 steam":
            send_steam()

        elif text == "🌐 epic store":
            send_message("https://store.epicgames.com")

        elif text == "🌐 steam store":
            send_message("https://store.steampowered.com")

        elif text in ["📌 wishlist", "/list"]:

            if watch:
                send_message("📌 Watchlist:\n" + "\n".join(watch))
            else:
                send_message("📭 Empty")


        elif text in ["❓ help", "/help"]:

            send_message(
                "🤖 Commands:\n\n"
                "/deals\n"
                "/details\n"
                "/add name\n"
                "/remove name\n"
                "/list"
            )


        elif text.startswith("/add "):

            name = text[5:]

            if name not in watch:
                watch.append(name)
                save_file(WATCH_FILE, watch)
                send_message(f"✅ Added: {name}")


        elif text.startswith("/remove "):

            name = text[8:]

            if name in watch:
                watch.remove(name)
                save_file(WATCH_FILE, watch)
                send_message(f"❌ Removed: {name}")



    check_daily()



if __name__ == "__main__":
    main()
