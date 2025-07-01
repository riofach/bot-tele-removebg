"""
File ini berisi logika inti untuk menghapus background gambar.
"""

from rembg import remove, new_session
from PIL import Image
import io

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
        # Menghapus background dengan semua pengaturan lanjutan
        output_image_bytes = remove(
            input_image_bytes,
            session=session,
            alpha_matting=ALPHA_MATTING_ENABLED,
            alpha_matting_foreground_threshold=ALPHA_MATTING_FOREGROUND_THRESHOLD,
            alpha_matting_background_threshold=ALPHA_MATTING_BACKGROUND_THRESHOLD,
            alpha_matting_erode_size=ALPHA_MATTING_ERODE_SIZE,
            post_process_mask=POST_PROCESS_MASK_ENABLED,
        )

        # Verifikasi output untuk memastikan hasilnya adalah gambar yang valid
        # dengan membuka dan menyimpannya kembali. Ini juga memastikan formatnya benar.
        with Image.open(io.BytesIO(output_image_bytes)) as img:
            # Pastikan formatnya adalah PNG untuk mendukung transparansi
            if img.format != "PNG":
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                output_image_bytes = buffer.getvalue()

        return output_image_bytes

    except Exception as e:
        # Jika terjadi error saat pemrosesan, kita bisa menanganinya di sini.
        # Untuk saat ini, kita hanya akan print error dan raise kembali.
        print(f"Error saat memproses gambar: {e}")
        raise
