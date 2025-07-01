"""
File ini berisi logika inti untuk menghapus background gambar.
"""

from rembg import remove, new_session
from PIL import Image, ImageColor
import io
import numpy as np
import cv2

# Tentukan model yang akan digunakan. 'isnet-general-use' seringkali lebih presisi.
MODEL_NAME = "isnet-general-use"

# --- Pengaturan Lanjutan untuk Hasil Potongan Paling Bersih ---

# 1. Alpha Matting dengan parameter 'agresif' untuk memisahkan objek dengan tegas.
ALPHA_MATTING_ENABLED = True
ALPHA_MATTING_FOREGROUND_THRESHOLD = 250  # Kembali ke nilai tinggi
ALPHA_MATTING_BACKGROUND_THRESHOLD = 20
ALPHA_MATTING_ERODE_SIZE = 5  # Kembali ke nilai kecil

# 2. Aktifkan langkah pemolesan akhir pada mask dari rembg.
POST_PROCESS_MASK_ENABLED = True

# 3. Threshold untuk 'Hard Cut' mask kita.
HARDEN_MASK_THRESHOLD = 128


def harden_mask(image_bytes: bytes, threshold: int) -> bytes:
    """
    Membuat tepian mask menjadi keras (tanpa gradasi) dengan thresholding.
    Ini menghilangkan semua piksel semi-transparan untuk hasil potongan yang sangat bersih.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img_np = np.array(img)

        alpha = img_np[:, :, 3]

        # Terapkan thresholding: nilai di atas threshold jadi 255, di bawahnya jadi 0
        _, new_alpha = cv2.threshold(alpha, threshold, 255, cv2.THRESH_BINARY)

        # Ganti alpha channel lama dengan yang sudah di-threshold
        img_np[:, :, 3] = new_alpha

        new_img = Image.fromarray(img_np, "RGBA")

        buffer = io.BytesIO()
        new_img.save(buffer, format="PNG")
        return buffer.getvalue()

    except Exception as e:
        print(f"Gagal mengeraskan mask: {e}. Mengembalikan gambar asli.")
        return image_bytes


def suppress_color_spill(image_bytes: bytes) -> bytes:
    """
    Pembersih noda digital: Mengurangi 'color spill' dari latar belakang ke objek.
    Ini adalah langkah post-processing canggih untuk membersihkan tepian.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img_np = np.array(img)

        # Ekstrak channel RGB dan Alpha
        rgb = img_np[:, :, :3]
        alpha = img_np[:, :, 3]

        # Buat mask untuk piksel yang memiliki transparansi (area tepian)
        spill_mask = (alpha > 0) & (alpha < 255)

        # Buat mask untuk piksel yang sepenuhnya solid (inti objek)
        solid_mask = alpha == 255

        # Dapatkan warna rata-rata dari inti objek. Ini akan menjadi warna 'pembersih'.
        # Kita menggunakan median untuk menghindari pengaruh warna outlier.
        median_color = np.median(rgb[solid_mask], axis=0)

        # Untuk setiap piksel di area tepian, campurkan warnanya dengan warna inti objek
        # Semakin transparan pikselnya, semakin banyak warna inti yang dicampurkan.
        for i in range(3):  # Loop untuk R, G, B
            channel = rgb[:, :, i]
            # Terapkan warna pembersih ke area tepian
            channel[spill_mask] = np.clip(
                channel[spill_mask] * 0.3 + median_color[i] * 0.7, 0, 255
            )

        # Gabungkan kembali channel RGB yang sudah dibersihkan dengan Alpha asli
        new_img_np = np.dstack((rgb.astype(np.uint8), alpha))
        new_img = Image.fromarray(new_img_np, "RGBA")

        # Simpan hasilnya ke bytes
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
# Ini lebih efisien karena model hanya dimuat sekali saat aplikasi dimulai.
session = new_session(model_name=MODEL_NAME)


def remove_background(input_image_bytes: bytes) -> bytes:
    """
    Menerima byte gambar, menghapus latar belakangnya, dan mengembalikan byte gambar hasil.

    :param input_image_bytes: Gambar masukan dalam bentuk bytes.
    :return: Gambar hasil (PNG) dalam bentuk bytes dengan background transparan.
    """
    try:
        # Langkah 1: Hapus background dengan rembg
        initial_output_bytes = remove(
            input_image_bytes,
            session=session,
            alpha_matting=ALPHA_MATTING_ENABLED,
            alpha_matting_foreground_threshold=ALPHA_MATTING_FOREGROUND_THRESHOLD,
            alpha_matting_background_threshold=ALPHA_MATTING_BACKGROUND_THRESHOLD,
            alpha_matting_erode_size=ALPHA_MATTING_ERODE_SIZE,
            post_process_mask=POST_PROCESS_MASK_ENABLED,
        )

        # Langkah 2: Lakukan 'Hard Cut' pada mask untuk potongan yang super bersih
        hardened_bytes = harden_mask(initial_output_bytes, HARDEN_MASK_THRESHOLD)

        # Langkah 3: Lakukan pembersihan 'color spill'
        final_output_bytes = suppress_color_spill(hardened_bytes)

        return final_output_bytes

    except Exception as e:
        # Jika terjadi error saat pemrosesan, kita bisa menanganinya di sini.
        # Untuk saat ini, kita hanya akan print error dan raise kembali.
        print(f"Error saat memproses gambar: {e}")
        raise
