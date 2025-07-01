"""
File ini berisi logika inti untuk menghapus background gambar.
"""

from rembg import remove, new_session
from PIL import Image
import io
import numpy as np

# Tentukan model yang akan digunakan. 'isnet-general-use' seringkali lebih presisi.
MODEL_NAME = "isnet-general-use"

# --- Pengaturan Lanjutan untuk Hasil Maksimal ---

# 1. Aktifkan Alpha Matting untuk detail yang lebih halus.
ALPHA_MATTING_ENABLED = True
#    Parameter yang lebih 'ketat' untuk mendefinisikan area foreground dan background,
#    memaksa algoritma untuk lebih presisi.
ALPHA_MATTING_FOREGROUND_THRESHOLD = 250
ALPHA_MATTING_BACKGROUND_THRESHOLD = 20
#    Ukuran erosi yang lebih kecil untuk menangani detail yang sangat halus.
ALPHA_MATTING_ERODE_SIZE = 5

# 2. Aktifkan langkah pemolesan akhir pada mask.
#    Ini adalah kunci untuk menghaluskan tepian dan mengurangi 'color spill'.
POST_PROCESS_MASK_ENABLED = True


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
        # Langkah 1: Hapus background dengan rembg dan semua pengaturan lanjutan
        initial_output_bytes = remove(
            input_image_bytes,
            session=session,
            alpha_matting=ALPHA_MATTING_ENABLED,
            alpha_matting_foreground_threshold=ALPHA_MATTING_FOREGROUND_THRESHOLD,
            alpha_matting_background_threshold=ALPHA_MATTING_BACKGROUND_THRESHOLD,
            alpha_matting_erode_size=ALPHA_MATTING_ERODE_SIZE,
            post_process_mask=POST_PROCESS_MASK_ENABLED,
        )

        # Langkah 2: Lakukan pembersihan 'color spill' pada hasil rembg
        final_output_bytes = suppress_color_spill(initial_output_bytes)

        return final_output_bytes

    except Exception as e:
        # Jika terjadi error saat pemrosesan, kita bisa menanganinya di sini.
        # Untuk saat ini, kita hanya akan print error dan raise kembali.
        print(f"Error saat memproses gambar: {e}")
        raise
