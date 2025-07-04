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

# Muat model deteksi wajah Haar Cascade dari OpenCV
# Path ini akan bekerja jika opencv-python diinstal dengan benar
try:
    FACE_CASCADE = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
except Exception as e:
    print(f"Peringatan: Gagal memuat model deteksi wajah: {e}")
    FACE_CASCADE = None


def resize_pas_foto(image_bytes: bytes, size_key: str) -> bytes:
    """
    Mengubah ukuran gambar ke standar pas foto yang dipilih dengan deteksi wajah.
    Gambar akan di-crop secara cerdas untuk memastikan subjek berada di tengah
    dan memiliki rasio aspek yang benar sebelum di-resize.

    :param image_bytes: Gambar input dalam bentuk bytes.
    :param size_key: Kunci ukuran dari PAS_FOTO_SIZES (misal: '3x4').
    :return: Gambar yang sudah di-crop dan di-resize dalam format PNG bytes.
    """
    if size_key not in PAS_FOTO_SIZES:
        raise ValueError(f"Ukuran '{size_key}' tidak valid.")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img_np = np.array(img)

    target_cm = PAS_FOTO_SIZES[size_key]
    target_px_w = int((target_cm[0] / 2.54) * DPI)
    target_px_h = int((target_cm[1] / 2.54) * DPI)
    target_aspect_ratio = target_px_w / target_px_h

    # --- Logika Cropping Cerdas ---
    best_crop_box = None

    if FACE_CASCADE:
        # Konversi ke Grayscale untuk deteksi wajah
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY)
        faces = FACE_CASCADE.detectMultiScale(
            gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) > 0:
            # Ambil wajah terbesar
            main_face = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
            x, y, w, h = main_face
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            # Tentukan ukuran crop box, lebih besar dari wajah untuk menyertakan bahu
            crop_h = h * 2.5
            crop_w = crop_h * target_aspect_ratio

            # Jika hasil crop lebih besar dari gambar asli, sesuaikan
            if crop_w > img.width or crop_h > img.height:
                if (img.width / target_aspect_ratio) < img.height:
                    crop_w = img.width
                    crop_h = crop_w / target_aspect_ratio
                else:
                    crop_h = img.height
                    crop_w = crop_h * target_aspect_ratio

            # Hitung pojok kiri atas crop box
            crop_x1 = int(face_center_x - crop_w // 2)
            crop_y1 = int(face_center_y - crop_h // 2 * 0.8)  # Geser sedikit ke atas

            # Pastikan crop box tidak keluar dari gambar
            crop_x1 = max(0, crop_x1)
            crop_y1 = max(0, crop_y1)

            crop_x2 = int(crop_x1 + crop_w)
            crop_y2 = int(crop_y1 + crop_h)

            if crop_x2 > img.width:
                crop_x1 -= crop_x2 - img.width
            if crop_y2 > img.height:
                crop_y1 -= crop_y2 - img.height

            best_crop_box = (
                max(0, crop_x1),
                max(0, crop_y1),
                int(crop_x1 + crop_w),
                int(crop_y1 + crop_h),
            )

    # Fallback atau jika tidak ada wajah terdeteksi: Center Crop
    if not best_crop_box:
        img_w, img_h = img.size
        img_aspect_ratio = img_w / img_h

        if img_aspect_ratio > target_aspect_ratio:  # Gambar lebih lebar
            new_w = int(target_aspect_ratio * img_h)
            offset = (img_w - new_w) // 2
            best_crop_box = (offset, 0, offset + new_w, img_h)
        else:  # Gambar lebih tinggi atau sama
            new_h = int(img_w / target_aspect_ratio)
            offset = (img_h - new_h) // 2
            best_crop_box = (0, offset, img_w, offset + new_h)

    # Lakukan cropping
    cropped_img = img.crop(best_crop_box)

    # Resize gambar yang sudah di-crop ke ukuran final
    resized_img = cropped_img.resize(
        (target_px_w, target_px_h), Image.Resampling.LANCZOS
    )

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
