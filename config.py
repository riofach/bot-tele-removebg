"""
File untuk konfigurasi terpusat.
"""

import os
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

# Ambil token bot dari environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN tidak ditemukan! Mohon periksa file .env Anda."
    )
