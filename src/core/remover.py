"""
File ini berisi logika inti untuk menghapus background gambar.
"""

from rembg import remove, new_session
from PIL import Image, ImageColor
import io
import numpy as np
import cv2

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
