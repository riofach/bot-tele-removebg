"""
File ini berisi semua handler untuk perintah dan pesan dari user.
"""

import logging
from telegram import (
    Update,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.core.remover import (
    remove_background,
    apply_solid_background,
    resize_pas_foto,
    create_a4_pdf_sheet,
    PAS_FOTO_SIZES,
)
import io

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Keyboard & Tombol Universal ---
RESTART_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]]
)


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kembali ke menu utama dengan mengirim pesan baru tanpa menghapus pesan lama."""
    query = update.callback_query
    await query.answer()

    # Hapus tombol dari pesan sebelumnya agar tidak bisa diklik lagi
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(
            f"Tidak dapat mengedit reply_markup: {e}. Mungkin pesan tidak memiliki tombol."
        )

    user_name = update.effective_user.first_name
    keyboard = [
        [
            InlineKeyboardButton(
                "🖼️ Hapus Background Saja", callback_data="remove_bg_start"
            )
        ],
        [InlineKeyboardButton("📸 Buat Pas Foto", callback_data="pas_foto_start")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="help_command")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Kirim pesan menu utama yang baru
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 Halo, {user_name}!\n\n"
        'Saya adalah bot milik <a href="https://www.instagram.com/rrdtyaa_/">@rrdtyaa_</a> yang bisa menghapus dan mengganti background gambar. '
        "Silakan pilih salah satu menu di bawah ini.",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan sambutan saat perintah /start dijalankan."""
    user_name = update.effective_user.first_name
    keyboard = [
        [
            InlineKeyboardButton(
                "🖼️ Hapus Background Saja", callback_data="remove_bg_start"
            )
        ],
        [InlineKeyboardButton("📸 Buat Pas Foto", callback_data="pas_foto_start")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="help_command")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        f"👋 Halo, {user_name}!\n\n"
        'Saya adalah bot milik <a href="https://www.instagram.com/rrdtyaa_/">@rrdtyaa_</a> yang bisa menghapus dan mengganti background gambar. '
        "Silakan pilih salah satu menu di bawah ini.",
        reply_markup=reply_markup,
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan bantuan saat perintah /help dijalankan atau tombol Bantuan ditekan."""
    help_text = (
        "<b>Bantuan Bot</b>\n\n"
        "Bot ini memiliki dua fitur utama:\n\n"
        "1. <b>Hapus Background Cepat</b>\n"
        "   - Kirim foto apa saja langsung ke chat ini.\n"
        "   - Bot akan otomatis menghapus latarnya.\n"
        "   - Gunakan perintah <code>/bg [warna]</code> setelahnya untuk memberi warna solid (misal: <code>/bg red</code> atau <code>/bg #00FF00</code>).\n\n"
        "2. <b>Pembuat Pas Foto (Menu Utama)</b>\n"
        "   - Mulai dari tombol '📸 Buat Pas Foto'.\n"
        "   - Ikuti alur untuk memilih warna background, ukuran (2x3, 3x4, 4R, dll.), dan format output.\n"
        "   - Anda bisa mengunduh 1 foto atau mencetaknya dalam jumlah banyak di kertas A4 (format PDF)."
    )

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            help_text, reply_markup=RESTART_KEYBOARD, parse_mode="HTML"
        )
    else:
        await update.message.reply_html(help_text, reply_markup=RESTART_KEYBOARD)


async def simple_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan gambar untuk mode hapus background sederhana."""
    message = update.message
    processing_message = await message.reply_text("✨ Sedang memproses gambar Anda...")

    try:
        photo = message.photo[-1]
        photo_file = await photo.get_file()

        input_bytes_io = io.BytesIO()
        await photo_file.download_to_memory(input_bytes_io)
        input_bytes_io.seek(0)

        logger.info("Gambar berhasil diunduh, memulai proses penghapusan background...")

        output_bytes = remove_background(input_bytes_io.read())

        # Simpan gambar yang sudah diproses untuk digunakan oleh /bg
        context.user_data["last_processed_image"] = output_bytes

        logger.info("Background berhasil dihapus, mengirim gambar kembali ke user.")

        output_bytes_io = io.BytesIO(output_bytes)
        output_bytes_io.name = "removed_background.png"

        await message.reply_document(
            document=InputFile(output_bytes_io),
            caption="Ini dia hasilnya! Sekarang coba ganti latarnya dengan /bg [warna].",
            reply_markup=RESTART_KEYBOARD,
        )

    except Exception as e:
        logger.error(f"Gagal memproses gambar: {e}")
        await message.reply_text(
            "Maaf, terjadi kesalahan saat memproses gambar Anda.",
            reply_markup=RESTART_KEYBOARD,
        )
    finally:
        await context.bot.delete_message(
            chat_id=processing_message.chat_id, message_id=processing_message.message_id
        )

    return ConversationHandler.END


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
            reply_markup=RESTART_KEYBOARD,
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


# --- Alur Percakapan untuk Fitur Pas Foto ---

# Definisikan states untuk ConversationHandler
(
    GET_PHOTO,
    CONFIRM_BG_REMOVAL,
    CHOOSE_BG_OPTION,
    GET_BG_COLOR,
    ASK_SIZE,
    GET_SIZE,
    GET_PDF_COUNT,
    GET_SIMPLE_PHOTO,
) = range(8)

# Warna background default
BG_COLORS = {"Merah": "#FF0000", "Biru": "#0000FF", "Putih": "#FFFFFF"}


async def remove_bg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai alur hapus background sederhana."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="🖼️ Anda dalam mode Hapus Background.\n\nSilakan kirim sebuah foto."
    )
    return GET_SIMPLE_PHOTO


async def pas_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai alur pembuatan pas foto."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="📸 Baik, mari kita mulai. Silakan kirim satu foto Anda yang ingin dijadikan pas foto."
    )
    return GET_PHOTO


async def pas_foto_get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima foto dari user dan meminta konfirmasi untuk hapus background."""
    photo_file = await update.message.photo[-1].get_file()

    # Simpan file ID dan juga download byte-nya untuk penggunaan nanti
    input_stream = io.BytesIO()
    await photo_file.download_to_memory(input_stream)
    input_stream.seek(0)
    context.user_data["pas_foto_original_bytes"] = input_stream.read()

    # Hapus pesan asli dari user
    await update.message.delete()

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Ya, Hapus Background", callback_data="remove_bg_yes"
            ),
            InlineKeyboardButton("➡️ Tidak, Pakai Asli", callback_data="remove_bg_no"),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali ke Menu Utama", callback_data="back_to_start"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Kirim kembali foto yang sama dengan pertanyaan
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo_file.file_id,
        caption="""Oke, foto diterima.

Apakah Anda ingin menghapus background-nya? 
(Ini diperlukan jika Anda ingin mengganti warna latar).""",
        reply_markup=reply_markup,
    )

    return CONFIRM_BG_REMOVAL


async def handle_remove_bg_decision_yes(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Memproses keputusan user untuk menghapus background, lalu lanjut ke pilihan warna."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_caption(
        caption="⏳ Sedang memproses penghapusan background..."
    )

    try:
        input_bytes = context.user_data["pas_foto_original_bytes"]

        # Hapus background
        removed_bg_bytes = remove_background(input_bytes)
        context.user_data["pas_foto_image"] = (
            removed_bg_bytes  # Ini akan jadi basis untuk ganti warna
        )

        keyboard = [
            [
                InlineKeyboardButton("Ya, Ubah Background", callback_data="change_bg"),
                InlineKeyboardButton("Lewati (Transparan)", callback_data="skip_bg"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Ganti media foto dengan versi tanpa background
        media = InputMediaPhoto(
            media=io.BytesIO(removed_bg_bytes),
            caption="Background berhasil dihapus! Apakah Anda ingin mengubah warna latarnya?",
        )

        await query.message.edit_media(media=media, reply_markup=reply_markup)

        return CHOOSE_BG_OPTION

    except Exception as e:
        logger.error(f"Gagal di tahap remove_bg_yes: {e}")
        await query.message.edit_caption(
            caption="Maaf, terjadi kesalahan saat memproses foto Anda. Silakan coba lagi.",
            reply_markup=RESTART_KEYBOARD,
        )
        return ConversationHandler.END


async def handle_remove_bg_decision_no(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Memproses keputusan user untuk tidak menghapus background dan langsung ke pilihan ukuran."""
    query = update.callback_query
    await query.answer()

    # Gunakan gambar asli sebagai gambar final
    original_bytes = context.user_data["pas_foto_original_bytes"]
    context.user_data["pas_foto_image"] = original_bytes

    # Langsung ke step ASK_SIZE (mirip dengan skip_bg)
    return await pas_foto_ask_size(update, context)


async def pas_foto_bg_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pilihan pengguna: ubah background atau lewati."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "skip_bg":
        # Jangan edit pesan di sini, biarkan handler berikutnya yang melakukannya.
        return await pas_foto_ask_size(update, context)

    elif choice == "change_bg":
        buttons = [
            InlineKeyboardButton(name, callback_data=f"color_{code}")
            for name, code in BG_COLORS.items()
        ]
        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Gunakan edit_message_caption karena pesan yang diedit adalah foto
        await query.message.edit_caption(
            caption="Silakan pilih warna latar belakang yang diinginkan:",
            reply_markup=reply_markup,
        )
        return GET_BG_COLOR


async def pas_foto_get_bg_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengaplikasikan warna background dan langsung menampilkan pilihan ukuran."""
    query = update.callback_query
    await query.answer()
    color_code = query.data.split("_")[1]

    # Beri tahu pengguna bahwa proses sedang berjalan
    await query.message.edit_caption(
        caption="🎨 Menerapkan background & menyiapkan pilihan ukuran..."
    )

    try:
        # Dapatkan gambar dengan background transparan dari memory
        original_image = context.user_data["pas_foto_image"]
        # Aplikasikan warna background baru
        new_bg_image = apply_solid_background(original_image, color_code)
        # Simpan kembali gambar yang sudah berwarna ke memory
        context.user_data["pas_foto_image"] = new_bg_image

        # Siapkan keyboard untuk pilihan ukuran
        buttons = [
            InlineKeyboardButton(size, callback_data=f"size_{size}")
            for size in PAS_FOTO_SIZES.keys()
        ]
        keyboard = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Siapkan media foto baru untuk menggantikan yang lama
        media = InputMediaPhoto(
            media=io.BytesIO(new_bg_image),
            caption="Background berhasil diubah. Sekarang, silakan pilih ukuran pas foto yang Anda butuhkan:",
        )

        # Edit pesan yang ada dengan mengganti foto, caption, dan keyboard sekaligus
        await query.message.edit_media(media=media, reply_markup=reply_markup)

        # Lanjutkan ke state berikutnya untuk memilih ukuran
        return GET_SIZE

    except Exception as e:
        logger.error(f"Gagal di tahap GET_BG_COLOR: {e}")
        await query.message.edit_caption(
            caption="Maaf, terjadi kesalahan. Proses dibatalkan."
        )
        return ConversationHandler.END


async def pas_foto_ask_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan pilihan ukuran pas foto (digunakan jika user melewati tahap ganti background)."""
    buttons = [
        InlineKeyboardButton(size, callback_data=f"size_{size}")
        for size in PAS_FOTO_SIZES.keys()
    ]
    # Buat 3 kolom
    keyboard = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Tentukan apakah akan edit pesan atau kirim baru
    message_text = "Baik, menggunakan foto ini. Sekarang, silakan pilih ukuran pas foto yang Anda butuhkan:"
    if update.callback_query:
        # Gunakan edit_message_caption karena pesan yang diedit kemungkinan besar adalah foto
        await update.callback_query.message.edit_caption(
            caption=message_text, reply_markup=reply_markup
        )
    else:
        # Fallback jika dipanggil tanpa query (seharusnya tidak terjadi di alur ini)
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)

    return GET_SIZE


async def pas_foto_get_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menangani pilihan ukuran, memproses resize, dan langsung meminta jumlah untuk PDF.
    """
    query = update.callback_query
    await query.answer()
    size_key = query.data.split("_")[1]
    context.user_data["pas_foto_size"] = size_key
    image_bytes = context.user_data["pas_foto_image"]

    await query.message.edit_caption(
        caption=f"Ukuran {size_key} dipilih. ⏳ Memproses gambar..."
    )

    try:
        resized_bytes = resize_pas_foto(image_bytes, size_key)
        context.user_data["pas_foto_resized"] = resized_bytes

        # Langsung tanyakan jumlah PDF
        await query.message.edit_caption(
            caption=f"Ukuran {size_key} siap. Mau dicetak berapa banyak foto dalam satu lembar A4? Silakan balas dengan angka (misal: 8)."
        )
        return GET_PDF_COUNT

    except Exception as e:
        logger.error(f"Gagal di tahap GET_SIZE (resizing): {e}")
        await query.message.edit_caption(
            "Maaf, terjadi kesalahan saat memproses ukuran. Proses dibatalkan.",
            reply_markup=RESTART_KEYBOARD,
        )
        return ConversationHandler.END


async def pas_foto_get_pdf_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membuat dan mengirim file PDF."""
    message = update.message
    try:
        count = int(message.text)
        if not 1 <= count <= 50:  # Batasi jumlah
            raise ValueError

        processing_message = await message.reply_text(
            f"Membuat lembar PDF dengan {count} foto..."
        )

        resized_bytes = context.user_data["pas_foto_resized"]
        size_key = context.user_data["pas_foto_size"]

        pdf_bytes = create_a4_pdf_sheet(resized_bytes, count, size_key)

        await message.reply_document(
            document=io.BytesIO(pdf_bytes),
            filename=f"pas_foto_{size_key}_A4.pdf",
            caption=f"Siap! Ini file PDF berisi {count} pas foto ukuran {size_key} untuk dicetak di kertas A4.",
            reply_markup=RESTART_KEYBOARD,
        )
        await context.bot.delete_message(
            chat_id=processing_message.chat_id, message_id=processing_message.message_id
        )

    except (ValueError, TypeError):
        await message.reply_text(
            "Input tidak valid. Mohon kirim sebuah angka saja (contoh: 8)."
        )
        return GET_PDF_COUNT  # Minta lagi
    except Exception as e:
        logger.error(f"Gagal di tahap GET_PDF_COUNT: {e}")
        await message.reply_text(
            "Maaf, terjadi kesalahan saat membuat PDF. Proses dibatalkan."
        )

    # Hapus data setelah selesai atau gagal
    for key in ["pas_foto_image", "pas_foto_size", "pas_foto_resized"]:
        context.user_data.pop(key, None)

    return ConversationHandler.END


async def pas_foto_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membatalkan alur percakapan."""
    await update.message.reply_text("Proses pembuatan pas foto telah dibatalkan.")
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Mencatat semua error yang terjadi."""
    logger.error("Exception while handling an update:", exc_info=context.error)
