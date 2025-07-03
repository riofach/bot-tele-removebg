"""
File utama untuk menjalankan bot Telegram.
"""

import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

# Import konfigurasi dan handler
import config
from src.bot.handlers import (
    start_handler,
    help_handler,
    simple_image_handler,
    error_handler,
    bg_handler,
    back_to_start,
    # --- Impor untuk Fitur Hapus Background Sederhana ---
    remove_bg_start,
    GET_SIMPLE_PHOTO,
    # --- Impor untuk Fitur Pas Foto ---
    pas_foto_start,
    pas_foto_get_photo,
    pas_foto_bg_option,
    pas_foto_get_bg_color,
    pas_foto_get_size,
    pas_foto_get_output_format,
    pas_foto_get_pdf_count,
    pas_foto_cancel,
    GET_PHOTO,
    CHOOSE_BG_OPTION,
    GET_BG_COLOR,
    GET_SIZE,
    GET_OUTPUT_FORMAT,
    GET_PDF_COUNT,
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

    # --- Handler untuk Fitur Pas Foto ---
    pas_foto_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(pas_foto_start, pattern="^pas_foto_start$")],
        states={
            GET_PHOTO: [MessageHandler(filters.PHOTO, pas_foto_get_photo)],
            CHOOSE_BG_OPTION: [
                CallbackQueryHandler(pas_foto_bg_option, pattern="^change_bg|skip_bg$")
            ],
            GET_BG_COLOR: [
                CallbackQueryHandler(pas_foto_get_bg_color, pattern="^color_")
            ],
            GET_SIZE: [CallbackQueryHandler(pas_foto_get_size, pattern="^size_")],
            GET_OUTPUT_FORMAT: [
                CallbackQueryHandler(
                    pas_foto_get_output_format, pattern="^output_single|output_pdf$"
                )
            ],
            GET_PDF_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pas_foto_get_pdf_count)
            ],
        },
        fallbacks=[CommandHandler("batal", pas_foto_cancel)],
    )

    # --- Handler untuk Fitur Hapus Background Sederhana ---
    simple_remove_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(remove_bg_start, pattern="^remove_bg_start$")
        ],
        states={
            GET_SIMPLE_PHOTO: [MessageHandler(filters.PHOTO, simple_image_handler)],
        },
        fallbacks=[CommandHandler("batal", pas_foto_cancel)],
    )

    application.add_handler(pas_foto_conv)
    application.add_handler(simple_remove_conv)

    # --- Handler Reguler ---
    application.add_handler(CommandHandler("start", start_handler))
    # Handler untuk tombol kembali ke menu utama
    application.add_handler(
        CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
    )
    # Handler untuk tombol bantuan dari menu start
    application.add_handler(
        CallbackQueryHandler(help_handler, pattern="^help_command$")
    )
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("bg", bg_handler))

    # Handler global untuk gambar dihapus agar bot tidak merespons tanpa mode
    # application.add_handler(MessageHandler(filters.PHOTO, image_handler))

    # Error handler
    application.add_error_handler(error_handler)

    # Jalankan bot sampai user menekan Ctrl+C
    application.run_polling()

    logger.info("Bot berhenti.")


if __name__ == "__main__":
    main()
