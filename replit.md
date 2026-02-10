# Game Deals Telegram Bot

## Overview
A Telegram bot that monitors game deals (Epic, Steam) and notifies users via Telegram. Users can manage a watchlist of games through bot commands.

## Architecture
- **Language**: Python 3.12
- **Dependencies**: `requests` (managed via uv/pyproject.toml)
- **Runtime**: Long-running console process (polls Telegram every 10 seconds)
- **Data Storage**: JSON files (`sent_deals.json`, `watchlist.json`, `price_history.json`, `last_update.txt`)

## Environment Variables (Secrets)
- `BOT_TOKEN` - Telegram Bot API token
- `CHAT_ID` - Telegram chat ID for notifications

## Bot Commands
- `/add <game>` - Add a game to the watchlist
- `/remove <game>` - Remove a game from the watchlist
- `/clear` - Clear the entire watchlist
- `/list` - Show all games in the watchlist

## Key Files
- `bot.py` - Main bot logic (commands, deal checking, Telegram API)
- `watchlist.json` - User's game watchlist
- `sent_deals.json` - Tracks already-sent deal notifications
- `price_history.json` - Historical price data
- `last_update.txt` - Telegram update offset tracking
