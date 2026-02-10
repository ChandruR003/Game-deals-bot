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
SENT_FILE = "sent_deals.json"
PRICE_FILE = "price_history.json"

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

# ================= UPDATES ================= #
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

def load_sent():
    return load_file(SENT_FILE, [])

def save_sent(data):
    save_file(SENT_FILE, data)

def load_prices():
    return load_file(PRICE_FILE, {})

def save_prices(data):
    save_file(PRICE_FILE, data)

# ================= TELEGRAM UPDATES ================= #
def get_updates():
    last = load_update()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last + 1, "timeout": 10}
    data = requests.get(url, params=params).json()
    if not data.get("result"):
        return []
    updates = data["result"]
    save_update(updates[-1]["update_id"])
    return updates

# ================= EPIC GAMES ================= #
def get_epic():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    data = requests.get(url).json()
    games = data["data"]["Catalog"]["searchStore"]["elements"]

    free_games, discount_games = [], []

    for g in games:
        title = g["title"]
        price = g["price"]["totalPrice"]
        orig = price["originalPrice"] / 100
        now = price["discountPrice"] / 100
        off = int(price["discount"])

        # End date
        end = "Unknown"
        promos = g.get("promotions")
        if promos and promos.get("promotionalOffers"):
            p = promos["promotionalOffers"]
            if p and p[0].get("promotionalOffers"):
                end = p[0]["promotionalOffers"][0]["endDate"][:10]

        # Image
        image = g.get("keyImages")[0]["url"] if g.get("keyImages") else None

        # Free
        if now == 0:
            free_games.append({
                "id": f"epic_{title}",
                "name": title,
                "img": image,
                "end": end
            })
        # Discount >=30%
        elif off >= 30:
            discount_games.append({
                "id": f"epic_{title}",
                "name": title,
                "orig": orig,
                "now": now,
                "off": off,
                "img": image,
                "end": end
            })

    return free_games, discount_games

# ================= STEAM ================= #
def get_steam():
    url = "https://store.steampowered.com/api/featuredcategories?cc=IN"
    data = requests.get(url).json()
    items = data["specials"]["items"]

    free_games, discount_games = [], []

    for g in items[:30]:
        name = g["name"]
        orig = g["original_price"] / 100
        now = g["final_price"] / 100
        off = g["discount_percent"]
        img = g["header_image"]

        # Free
        if now == 0:
            free_games.append({
                "id": f"steam_free_{g['id']}",
                "name": name,
                "img": img
            })
        # Discount >=30%
        elif off >= 30:
            discount_games.append({
                "id": f"steam_{g['id']}",
                "name": name,
                "orig": orig,
                "now": now,
                "off": off,
                "img": img
            })

    return free_games, discount_games

# ================= DEALS ================= #
def send_deals():
    e_free, e_discount = get_epic()
    s_free, s_discount = get_steam()

    # Free Epic
    for g in e_free[:5]:
        txt = f"🆓 <b>{g['name']}</b>\nEnds: {g['end']}"
        send_photo(txt, g["img"] if g["img"] else "")

    # Hot Epic Discount
    for g in e_discount[:3]:
        txt = f"🔥 <b>{g['name']}</b>\n₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)\nEnds: {g['end']}"
        send_photo(txt, g["img"] if g["img"] else "")

    # Free Steam
    for g in s_free[:5]:
        txt = f"🆓 <b>{g['name']}</b>"
        send_photo(txt, g["img"] if g["img"] else "")

    # Hot Steam Discount
    for g in s_discount[:3]:
        txt = f"🔥 <b>{g['name']}</b>\n₹{g['orig']} → ₹{g['now']} ({g['off']}% OFF)"
        send_photo(txt, g["img"] if g["img"] else "")

# ================= DETAILS ================= #
def send_details():
    e_free, e_discount = get_epic()
    s_free, s_discount = get_steam()

    msg = "📜 <b>All Deals</b>\n\n"
    msg += "🟦 Epic\n"
    i = 1
    for g in e_free + e_discount:
        line = f"{i}. {g['name']}"
        if 'now' in g:
            line += f" — ₹{g['now']} ({g['off']}%) Ends: {g['end']}"
        i += 1
        msg += line + "\n"

    msg += "\n🟩 Steam\n"
    i = 1
    for g in s_free + s_discount:
        line = f"{i}. {g['name']}"
        if 'now' in g:
            line += f" — ₹{g['now']} ({g['off']}%)"
        i += 1
        msg += line + "\n"

    send_message(msg)

# ================= WATCHLIST & DAILY ================= #
def check_daily_and_watch():
    sent = load_sent()
    prices = load_prices()
    watchlist = load_file(WATCH_FILE, [])

    e_free, e_discount = get_epic()
    s_free, s_discount = get_steam()

    new_sent = sent.copy()
    messages = []

    # EPIC
    for g in e_free + e_discount:
        if g["id"] not in sent:
            if 'now' in g:
                line = f"{g['name']} — ₹{g['now']} ({g['off']}% OFF) Ends: {g['end']}"
            else:
                line = f"{g['name']} — FREE Ends: {g['end']}"
            messages.append(f"🟦 {line}")
            new_sent.append(g["id"])

    # STEAM
    for g in s_free + s_discount:
        if g["id"] not in sent:
            if 'now' in g:
                line = f"{g['name']} — ₹{g['now']} ({g['off']}% OFF)"
            else:
                line = f"{g['name']} — FREE"
            messages.append(f"🟩 {line}")
            new_sent.append(g["id"])

    # WATCHLIST ALERTS
    for alert in messages:
        for w in watchlist:
            if w.lower() in alert.lower():
                send_message(f"🔔 WATCH ALERT!\n{alert}")

    # SEND AUTOMATIC NEW DEALS
    for msg_text in messages:
        send_message(msg_text)

    save_sent(new_sent)
    save_prices(prices)

    # DAILY 9PM SUMMARY
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    today = now.strftime("%Y-%m-%d")
    last = load_daily()
    if now.hour == 21 and last != today:
        send_deals()
        save_daily(today)

# ================= MAIN ================= #
def main():
    watchlist = load_file(WATCH_FILE, [])

    updates = get_updates()

    for u in updates:
        if "message" not in u:
            continue
        text = u["message"].get("text", "").strip().lower()

        # START
        if text == "/start":
            send_message("👋 Welcome to Game Deals Bot!")
            send_menu()
            continue

        # MENU OPTIONS
        if text in ["🔥 deals", "/deals"]:
            send_deals()
        elif text in ["📜 details", "/details"]:
            send_details()
        elif text == "🟦 epic":
            send_details()  # For simplicity, can call send_epic_specific if needed
        elif text == "🟩 steam":
            send_details()
        elif text == "🌐 epic store":
            send_message("https://store.epicgames.com")
        elif text == "🌐 steam store":
            send_message("https://store.steampowered.com")
        elif text in ["📌 wishlist", "/list"]:
            if watchlist:
                send_message("📌 Watchlist:\n" + "\n".join(watchlist))
            else:
                send_message("📭 Empty")
        elif text in ["❓ help", "/help"]:
            send_message(
                "🤖 Commands:\n"
                "/deals\n"
                "/details\n"
                "/add name\n"
                "/remove name\n"
                "/list"
            )
        # ADD/REMOVE
        elif text.startswith("/add "):
            name = text[5:]
            if name not in watchlist:
                watchlist.append(name)
                save_file(WATCH_FILE, watchlist)
                send_message(f"✅ Added: {name}")
        elif text.startswith("/remove "):
            name = text[8:]
            if name in watchlist:
                watchlist.remove(name)
                save_file(WATCH_FILE, watchlist)
                send_message(f"❌ Removed: {name}")

    # Automatic deals & daily summary
    check_daily_and_watch()

if __name__ == "__main__":
    main()
