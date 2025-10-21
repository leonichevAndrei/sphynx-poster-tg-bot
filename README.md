# 🐈 Sphynx Poster TG Bot

Telegram bot that automatically posts daily sphynx cat photos to a channel.

## Features
- Scheduled posting (e.g., 10 images/day)
- Sources: local folder or external URL list
- Simple configuration via environment variables

## Quick start
> This project is provided for portfolio/demo purposes.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
python bot.py
