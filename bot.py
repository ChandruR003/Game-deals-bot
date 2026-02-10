import requests
import os
import json
import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCH_FILE = "watchlist.json"
DAILY_FILE = "last_daily.txt"
UPDATE_FILE = "last_update.txt"


# ---------------- TELEGRAM ---------------- #

def send_message(text, buttons=None):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    if buttons:
        data["reply_markup"] = json.dumps({
            "inline_keyboard": buttons
        })

    requests.post(url, data=data)


def send_photo(text, image, buttons=None):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {
        "chat_id": CHAT_ID,
        "caption": text,
        "photo": image,
        "parse_mode": "HTML"
    }

    if buttons:
        data["reply_markup"] = json.dumps({
            "inline_keyboard": buttons
        })

    requests.post(url, data=data)


# ---------------- STORAGE ---------------- #

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


# ---------------- TELEGRAM ---------------- #

def answer_callback(cid):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": cid}

    requests.post(url, data=data)


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


# ---------------- EPIC ---------------- #

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

        # -------- SAFE END DATE --------
        end = "Unknown"

        promos_data = g.get("promotions")

        if promos_data and promos_data.get("promotionalOffers"):
            promos = promos_data["promotionalOffers"]

            if promos and promos[0].get("promotionalOffers"):
                end = promos[0]["promotionalOffers"][0]["endDate"][:10]

        # -------- SAFE IMAGE --------
        image = None

        if g.get("keyImages"):
            image = g["keyImages"][0]["url"]

        # -------- FREE --------
        if now == 0:

            free.append({
                "name": title,
                "img": None,
                "end": end
            })

        # -------- DEALS --------
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


# ---------------- STEAM ---------------- #

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


# ---------------- DEALS ---------------- #

def send_deals():

    e_free, e_hot, _, _ = get_epic()
    s_free, s_hot, _, _ = get_steam()

    send_message(
        "🎮 <b>Game Deals</b>",
        buttons=[
            [{"text": "🟦 Epic", "callback_data": "epic"}],
            [{"text": "🟩 Steam", "callback_data": "steam"}],
            [{"text": "📜 Details", "callback_data": "details"}],
        ]
    )

    for g in e_hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)\n"
            f"Ends: {g['end']}"
        )

        send_photo(
            txt,
            g["img"],
            [[{"text": "🟦 Epic Store", "url": "https://store.epicgames.com"}]]
        )

    for g in s_hot:

        txt = (
            f"🔥 <b>{g['name']}</b>\n"
            f"₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)"
        )

        send_photo(
            txt,
            g["img"],
            [[{"text": "🟩 Steam Store", "url": "https://store.steampowered.com"}]]
        )


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


# ---------------- DETAILS ---------------- #

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


# ---------------- DAILY ---------------- #

def check_daily():

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

    today = now.strftime("%Y-%m-%d")

    last = load_daily()

    if now.hour == 21 and last != today:

        send_deals()

        save_daily(today)


# ---------------- MAIN ---------------- #

def main():

    watch = load_file(WATCH_FILE, [])

    updates = get_updates()

    for u in updates:

        # BUTTONS
        if "callback_query" in u:

            cb = u["callback_query"]

            answer_callback(cb["id"])

            data = cb["data"]

            if data == "epic":
                send_epic()

            elif data == "steam":
                send_steam()

            elif data == "details":
                send_details()

            continue


        # MESSAGES
        if "message" not in u:
            continue

        text = u["message"].get("text", "").lower()


        if text == "/deals":
            send_deals()


        elif text == "/details":
            send_details()


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


        elif text == "/list":

            if watch:
                send_message("📌 Watchlist:\n" + "\n".join(watch))
            else:
                send_message("📭 Empty")


        elif text == "/help":

            send_message(
                "🤖 Commands:\n"
                "/deals\n"
                "/details\n"
                "/add name\n"
                "/remove name\n"
                "/list"
            )

    check_daily()


if __name__ == "__main__":
    main()
