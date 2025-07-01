"""
File utama untuk menjalankan bot Telegram.
"""

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Import konfigurasi dan handler yang sudah disederhanakan
import config
from src.bot.handlers import (
    start_handler,
    help_handler,
    image_handler,
    error_handler,
    bg_handler,
)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """
    Fungsi utama untuk menjalankan bot.
    """
    logger.info("Bot dimulai...")

    # Buat aplikasi bot
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Daftarkan handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("bg", bg_handler))

    # Handler untuk pesan berupa gambar
    application.add_handler(MessageHandler(filters.PHOTO, image_handler))

    # Error handler
    application.add_error_handler(error_handler)

    # Jalankan bot sampai user menekan Ctrl+C
    application.run_polling()

    logger.info("Bot berhenti.")


if __name__ == "__main__":
    main()
