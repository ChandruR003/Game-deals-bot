import requests
import os
import json
import time

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "sent_deals.json"
WATCH_FILE = "watchlist.json"
UPDATE_FILE = "last_update.txt"

# ---------------- TELEGRAM ----------------

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, data=data)


# ---------------- UPDATE SYSTEM ----------------

def load_last_update():
    try:
        with open(UPDATE_FILE, "r") as f:
            return int(f.read())
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
        "timeout": 20
    }

    r = requests.get(url, params=params).json()

    if not r.get("result"):
        return []

    updates = r["result"]

    newest = updates[-1]["update_id"]
    save_last_update(newest)

    return updates


# ---------------- WATCHLIST ----------------

def load_watchlist():
    try:
        with open(WATCH_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_watchlist(data):
    with open(WATCH_FILE, "w") as f:
        json.dump(data, f)


# ---------------- SENT DEALS ----------------

def load_sent():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_sent(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ---------------- COMMAND HANDLER ----------------

def handle_commands():

    watchlist = load_watchlist()

    updates = get_updates()

    for u in updates:

        if "message" not in u:
            continue

        msg = u["message"]
        text = msg.get("text", "").strip().lower()

        if not text.startswith("/"):
            continue

        parts = text.split(" ", 1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""


        # -------- ADD --------
        if cmd == "/add" and arg:

            if arg not in watchlist:
                watchlist.append(arg)
                save_watchlist(watchlist)

                send_telegram(f"✅ Added: <b>{arg}</b>")
            else:
                send_telegram(f"⚠️ Already in list: <b>{arg}</b>")


        # -------- REMOVE --------
        elif cmd == "/remove" and arg:

            if arg in watchlist:
                watchlist.remove(arg)
                save_watchlist(watchlist)

                send_telegram(f"❌ Removed: <b>{arg}</b>")
            else:
                send_telegram(f"⚠️ Not found: <b>{arg}</b>")


        # -------- CLEAR --------
        elif cmd == "/clear":

            watchlist.clear()
            save_watchlist(watchlist)

            send_telegram("🗑️ Watchlist cleared!")


        # -------- LIST --------
        elif cmd == "/list":

            if watchlist:

                msg = "📌 <b>Your Watchlist</b>\n\n"

                for i, g in enumerate(watchlist, 1):
                    msg += f"{i}. {g}\n"

                send_telegram(msg)

            else:
                send_telegram("📭 Watchlist is empty")

# STATUS
        elif cmd == "/status":
            send_telegram("✅ Bot is running fine.\n⏱ Last check: Active\n💻 Server: Online")


# ---------------- FAKE DEALS (TEMP) ----------------
# Replace later with real scraping

def get_epic_deals():
    return [], []


def get_steam_deals():
    return [], []


# ---------------- MAIN ----------------

def main():

    print("Bot Started...")

    while True:

        try:

            handle_commands()

            sent = load_sent()

            free_games, epic_discounts = get_epic_deals()
            steam_deals, steam_free = get_steam_deals()

            new_sent = sent.copy()

            # (Future deal logic here)

            save_sent(new_sent)

        except Exception as e:
            print("Error:", e)

        time.sleep(10)   # Run every 10 seconds


# ---------------- START ----------------

if __name__ == "__main__":
    main()
