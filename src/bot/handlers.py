"""
File ini berisi semua handler untuk perintah dan pesan dari user.
"""

import logging
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from src.core.remover import remove_background, apply_solid_background
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
        "Saya adalah bot yang bisa menghapus background gambar dengan presisi tinggi. "
        "Cukup kirimkan saya sebuah foto.\n\n"
        "Setelah itu, Anda bisa menggunakan perintah <code>/bg [warna]</code> "
        "untuk mengganti latarnya. Contoh: <code>/bg blue</code> atau <code>/bg #FF5733</code>."
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan bantuan saat perintah /help dijalankan."""
    await update.message.reply_html(
        "<b>Butuh bantuan?</b>\n\n"
        "1. Kirimkan gambar yang ingin Anda hapus latar belakangnya.\n"
        "2. Setelah saya kirim hasilnya, gunakan perintah <code>/bg [warna]</code> untuk mengganti latarnya.\n\n"
        "<b>Contoh Perintah:</b>\n"
        "<code>/bg red</code>\n"
        "<code>/bg #0000FF</code> (biru dengan kode hex)\n\n"
        "Saya akan berusaha memberikan hasil terbaik untuk semua jenis gambar."
    )


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan gambar dan memprosesnya."""
    message = update.message
    processing_message = await message.reply_text("✨ Sedang memproses gambar Anda...")

    try:
        photo = message.photo[-1]
        photo_file = await photo.get_file()

        input_bytes_io = io.BytesIO()
        await photo_file.download_to_memory(input_bytes_io)
        input_bytes_io.seek(0)

        logger.info("Gambar berhasil diunduh, memulai proses penghapusan background...")

        # Panggil fungsi remove_background (tanpa mode)
        output_bytes = remove_background(input_bytes_io.read())

        # Simpan gambar yang sudah diproses untuk digunakan oleh /bg
        context.user_data["last_processed_image"] = output_bytes

        logger.info("Background berhasil dihapus, mengirim gambar kembali ke user.")

        output_bytes_io = io.BytesIO(output_bytes)
        output_bytes_io.name = "removed_background.png"

        await message.reply_document(
            document=InputFile(output_bytes_io),
            caption="Ini dia hasilnya! Sekarang coba ganti latarnya dengan /bg [warna].",
        )

    except Exception as e:
        logger.error(f"Gagal memproses gambar: {e}")
        await message.reply_text("Maaf, terjadi kesalahan saat memproses gambar Anda.")
    finally:
        await context.bot.delete_message(
            chat_id=processing_message.chat_id, message_id=processing_message.message_id
        )


async def bg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengganti background dari gambar terakhir yang diproses."""
    message = update.message

    if "last_processed_image" not in context.user_data:
        await message.reply_text(
            "Anda harus mengirim sebuah gambar terlebih dahulu sebelum menggunakan perintah ini."
        )
        return

    if not context.args:
        await message.reply_html(
            "Mohon berikan warna. Contoh: <code>/bg blue</code> atau <code>/bg #FF0000</code>"
        )
        return

    color = context.args[0]
    processing_message = await message.reply_text(
        f"Mengganti background menjadi {color}..."
    )

    try:
        transparent_image_bytes = context.user_data["last_processed_image"]
        new_image_bytes = apply_solid_background(transparent_image_bytes, color)
        output_bytes_io = io.BytesIO(new_image_bytes)
        output_bytes_io.name = f"background_{color}.jpeg"
        await message.reply_photo(
            photo=InputFile(output_bytes_io),
            caption=f"Background berhasil diubah menjadi {color}! ✨",
        )
    except ValueError:
        await message.reply_text(
            f"Maaf, warna '{color}' sepertinya tidak valid. Coba gunakan nama warna (misal: red) atau kode hex (#FF0000)."
        )
    except Exception as e:
        logger.error(f"Gagal menerapkan background baru: {e}")
        await message.reply_text("Maaf, terjadi kesalahan saat mengubah background.")
    finally:
        await context.bot.delete_message(
            chat_id=processing_message.chat_id, message_id=processing_message.message_id
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Mencatat semua error yang terjadi."""
    logger.error("Exception while handling an update:", exc_info=context.error)
