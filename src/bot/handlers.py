"""
File ini berisi semua handler untuk perintah dan pesan dari user.
"""

import logging
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from src.core.remover import remove_background
import io

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan sambutan saat perintah /start dijalankan."""
    user_name = update.effective_user.first_name
    await update.message.reply_html(
        f"👋 Halo, {user_name}!\n\n"
        "Saya adalah bot yang bisa menghapus background gambar. "
        "Cukup kirimkan saya sebuah foto, dan saya akan mengembalikannya dengan "
        "latar belakang transparan (format PNG).\n\n"
        "Tunggu apa lagi? Yuk, coba kirim gambar!"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan bantuan saat perintah /help dijalankan."""
    await update.message.reply_text(
        "Butuh bantuan?\n\n"
        "Cukup kirimkan gambar yang ingin Anda hapus latar belakangnya. "
        "Saya akan otomatis memprosesnya. Pastikan gambar yang dikirim memiliki "
        "objek/subjek yang jelas agar hasilnya maksimal."
    )


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan gambar yang dikirim oleh pengguna."""
    message = update.message

    # 1. Beri tahu user bahwa gambar sedang diproses
    processing_message = await message.reply_text(
        "Sedang memproses gambar, mohon tunggu..."
    )

    try:
        # 2. Dapatkan objek file foto dengan resolusi tertinggi
        photo_file = await message.photo[-1].get_file()

        # 3. Unduh gambar ke dalam memori (sebagai bytes)
        input_bytes_io = io.BytesIO()
        await photo_file.download_to_memory(input_bytes_io)
        input_bytes_io.seek(0)

        logger.info("Gambar berhasil diunduh, memulai proses penghapusan background...")

        # 4. Panggil fungsi remove_background
        output_bytes = remove_background(input_bytes_io.read())

        logger.info("Background berhasil dihapus, mengirim gambar kembali ke user.")

        # 5. Kirim kembali gambar hasil sebagai file
        output_bytes_io = io.BytesIO(output_bytes)
        output_bytes_io.name = "removed_background.png"

        await message.reply_document(
            document=InputFile(output_bytes_io),
            caption="Ini dia hasilnya! ✨",
        )

    except Exception as e:
        logger.error(f"Gagal memproses gambar: {e}")
        await message.reply_text(
            "Maaf, terjadi kesalahan saat memproses gambar Anda. "
            "Coba lagi dengan gambar lain."
        )
    finally:
        # 6. Hapus pesan "sedang memproses"
        await context.bot.delete_message(
            chat_id=processing_message.chat_id, message_id=processing_message.message_id
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Mencatat semua error yang terjadi."""
    logger.error("Exception while handling an update:", exc_info=context.error)
