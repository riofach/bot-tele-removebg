"""
File ini berisi logika inti untuk menghapus background gambar.
"""

from rembg import remove, new_session
from PIL import Image, ImageColor
import io
import numpy as np
import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Tentukan model yang akan digunakan.
MODEL_NAME = "isnet-general-use"

# --- Pengaturan Lanjutan untuk Hasil Presisi Tinggi ---
ALPHA_MATTING_FOREGROUND_THRESHOLD = 250
ALPHA_MATTING_BACKGROUND_THRESHOLD = 15
ALPHA_MATTING_ERODE_SIZE = 5
POST_PROCESS_MASK_ENABLED = True


def refine_mask(image_bytes: bytes) -> bytes:
    """
    Menyempurnakan alpha channel untuk tepian yang lebih jelas tanpa kehilangan detail,
    dengan meningkatkan kontras pada masker.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img_np = np.array(img)

        alpha = img_np[:, :, 3]

        # Tingkatkan kontras pada alpha channel.
        # Ini akan membuat area semi-transparan menjadi lebih solid atau lebih transparan,
        # menghasilkan tepian yang lebih tegas namun tetap menjaga detail.
        alpha_float = alpha.astype(float) / 255.0

        # Fungsi power < 1 akan mendorong nilai tengah ke arah 1 (lebih solid)
        refined_alpha_float = np.power(alpha_float, 0.75)

        new_alpha = (refined_alpha_float * 255).astype(np.uint8)

        # Ganti alpha channel lama dengan yang sudah disempurnakan
        img_np[:, :, 3] = new_alpha

        new_img = Image.fromarray(img_np, "RGBA")

        buffer = io.BytesIO()
        new_img.save(buffer, format="PNG")
        return buffer.getvalue()

    except Exception as e:
        print(f"Gagal menyempurnakan mask: {e}. Mengembalikan gambar asli.")
        return image_bytes


def suppress_color_spill(image_bytes: bytes) -> bytes:
    """
    Pembersih noda digital: Mengurangi 'color spill' dari latar belakang ke objek.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img_np = np.array(img)
        rgb = img_np[:, :, :3]
        alpha = img_np[:, :, 3]
        spill_mask = (alpha > 0) & (alpha < 255)
        solid_mask = alpha == 255
        if not np.any(solid_mask):  # Hindari error jika tidak ada area solid
            return image_bytes
        median_color = np.median(rgb[solid_mask], axis=0)
        for i in range(3):
            channel = rgb[:, :, i]
            channel[spill_mask] = np.clip(
                channel[spill_mask] * 0.3 + median_color[i] * 0.7, 0, 255
            )
        new_img_np = np.dstack((rgb.astype(np.uint8), alpha))
        new_img = Image.fromarray(new_img_np, "RGBA")
        buffer = io.BytesIO()
        new_img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        print(
            f"Gagal melakukan color spill suppression: {e}. Mengembalikan gambar asli."
        )
        return image_bytes


def apply_solid_background(image_bytes: bytes, color: str) -> bytes:
    """
    Mengganti background transparan dengan warna solid.

    :param image_bytes: Gambar PNG transparan dalam bentuk bytes.
    :param color: Nama warna (misal: 'red', 'blue') atau kode hex (misal: '#FF5733').
    :return: Gambar JPG dengan background baru dalam bentuk bytes.
    """
    try:
        # Buka gambar transparan
        foreground_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # Dapatkan warna dari input string
        # ImageColor akan menangani nama warna dan kode hex secara otomatis
        background_color = ImageColor.getrgb(color)

        # Buat gambar background baru dengan warna solid
        background_img = Image.new("RGBA", foreground_img.size, background_color)

        # Gabungkan background dengan gambar foreground
        # Alpha channel dari foreground_img digunakan sebagai mask
        composite_img = Image.alpha_composite(background_img, foreground_img)

        # Konversi ke RGB (format JPG tidak mendukung transparansi)
        final_img = composite_img.convert("RGB")

        # Simpan hasilnya ke bytes dengan format JPEG
        buffer = io.BytesIO()
        final_img.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()

    except ValueError:
        # Error ini terjadi jika string warna tidak valid
        raise ValueError(f"Warna '{color}' tidak dikenali.")
    except Exception as e:
        print(f"Gagal menerapkan background solid: {e}")
        raise


# --- Logika untuk Fitur Pas Foto ---

# Standar ukuran pas foto dalam cm (lebar, tinggi)
PAS_FOTO_SIZES = {
    # Ukuran KTP & SIM
    "2x3": (2.16, 2.79),
    "3x4": (2.79, 3.81),
    "4x6": (3.81, 5.59),
    # Ukuran Cetak Foto (R series)
    "2R": (6.35, 8.89),
    "3R": (8.89, 12.7),
    "4R": (10.16, 15.24),
    "5R": (12.7, 17.78),
}

DPI = 300  # Standar resolusi cetak


def resize_pas_foto(image_bytes: bytes, size_key: str) -> bytes:
    """
    Mengubah ukuran gambar ke standar pas foto yang dipilih.

    :param image_bytes: Gambar input dalam bentuk bytes.
    :param size_key: Kunci ukuran dari PAS_FOTO_SIZES (misal: '3x4').
    :return: Gambar yang sudah di-resize dalam format PNG bytes.
    """
    if size_key not in PAS_FOTO_SIZES:
        raise ValueError(f"Ukuran '{size_key}' tidak valid.")

    img = Image.open(io.BytesIO(image_bytes))
    target_cm = PAS_FOTO_SIZES[size_key]

    # Konversi cm ke pixel
    target_px_w = int((target_cm[0] / 2.54) * DPI)
    target_px_h = int((target_cm[1] / 2.54) * DPI)

    # Resize dengan antialiasing terbaik
    resized_img = img.resize((target_px_w, target_px_h), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    resized_img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_a4_pdf_sheet(resized_image_bytes: bytes, count: int, size_key: str) -> bytes:
    """
    Menyusun beberapa pas foto ke dalam satu lembar PDF ukuran A4.

    :param resized_image_bytes: Satu gambar pas foto yang sudah di-resize.
    :param count: Jumlah foto yang ingin dicetak di lembar A4.
    :param size_key: Kunci ukuran untuk mendapatkan dimensi asli dalam cm.
    :return: File PDF dalam bentuk bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    a4_width, a4_height = A4

    img_reader = io.BytesIO(resized_image_bytes)
    # Gunakan ImageReader dari reportlab untuk memproses gambar dari bytes
    img_for_draw = ImageReader(img_reader)
    img_width_cm, img_height_cm = PAS_FOTO_SIZES[size_key]

    # Margin (1 cm)
    margin_x = 1 * cm
    margin_y = 1 * cm

    # Area cetak
    printable_width = a4_width - (2 * margin_x)
    printable_height = a4_height - (2 * margin_y)

    # Posisi awal
    x = margin_x
    y = a4_height - margin_y - (img_height_cm * cm)

    for i in range(count):
        if x + (img_width_cm * cm) > a4_width - margin_x:
            # Pindah ke baris baru
            x = margin_x
            y -= img_height_cm * cm + (0.2 * cm)  # Beri sedikit jarak antar baris

        if y < margin_y:
            # Halaman penuh, hentikan (atau buat halaman baru)
            break

        c.drawImage(
            img_for_draw,
            x,
            y,
            width=img_width_cm * cm,
            height=img_height_cm * cm,
            mask="auto",
        )
        img_reader.seek(0)  # Reset reader untuk penggunaan selanjutnya
        x += img_width_cm * cm + (0.2 * cm)  # Beri sedikit jarak antar kolom

    c.showPage()
    c.save()

    return buffer.getvalue()


# Buat sesi rembg dengan model yang spesifik.
session = new_session(model_name=MODEL_NAME)


def remove_background(input_image_bytes: bytes) -> bytes:
    """
    Menerima byte gambar, menghapus latarnya, dan mengembalikan hasil yang presisi.
    """
    try:
        # Langkah 1: Hapus background dengan rembg
        initial_output_bytes = remove(
            input_image_bytes,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=ALPHA_MATTING_FOREGROUND_THRESHOLD,
            alpha_matting_background_threshold=ALPHA_MATTING_BACKGROUND_THRESHOLD,
            alpha_matting_erode_size=ALPHA_MATTING_ERODE_SIZE,
            post_process_mask=POST_PROCESS_MASK_ENABLED,
        )

        # Langkah 2: Sempurnakan mask untuk tepian yang lebih tegas namun menjaga detail
        refined_bytes = refine_mask(initial_output_bytes)

        # Langkah 3: Lakukan pembersihan 'color spill'
        final_output_bytes = suppress_color_spill(refined_bytes)

        return final_output_bytes

    except Exception as e:
        print(f"Error saat memproses gambar: {e}")
        raise
