# Bot Telegram Background Remover

Bot Telegram canggih yang mampu menghapus latar belakang gambar dengan presisi tinggi dan menggantinya dengan warna solid sesuai keinginan pengguna. Dibangun menggunakan Python, `python-telegram-bot`, dan `rembg`.

![Contoh Hasil](https://i.imgur.com/uS3AN3i.png)
_Contoh: Hasil potongan presisi pada objek dengan detail halus._

---

## ✨ Fitur Utama

- **Penghapusan Latar Belakang Cerdas:** Menggunakan model AI (`isnet-general-use`) dengan alur kerja pemrosesan berlapis untuk hasil yang optimal di berbagai jenis gambar.
  - **Penyempurnaan Masker:** Secara otomatis mempertajam tepian objek tanpa menghilangkan detail halus seperti bulu atau bayangan.
  - **Penekanan Tumpahan Warna:** Membersihkan sisa-sisa warna dari latar belakang asli yang sering menempel di tepian objek.
- **Ganti Warna Background:** Setelah latar belakang dihapus, pengguna dapat dengan mudah menggantinya dengan warna solid apa pun menggunakan perintah sederhana.
- **Interaktif & Mudah Digunakan:** Cukup kirim gambar, dan ikuti instruksi. Tidak perlu perintah yang rumit.
- **Tanpa Penurunan Kualitas:** Bot memproses gambar asli dan mempertahankan kualitasnya.

## 🛠️ Tech Stack

- **Bahasa:** Python 3.8+
- **Framework Bot:** `python-telegram-bot`
- **Inti AI:** `rembg`
- **Pemrosesan Gambar:** `Pillow`, `NumPy`, `OpenCV`
- **Manajemen Kredensial:** `python-dotenv`
- **Lingkungan Virtual:** `venv`

## ⚙️ Instalasi

Ikuti langkah-langkah berikut untuk menjalankan bot di lingkungan lokal Anda.

**1. Clone Repositori (Opsional)**
Jika Anda memiliki Git, clone repositori ini. Jika tidak, cukup unduh dan ekstrak folder proyek.

```bash
git clone [URL_REPOSITORI_ANDA]
cd bot-tele-removebg
```

**2. Buat & Aktifkan Virtual Environment**
Sangat disarankan untuk menggunakan lingkungan virtual untuk mengisolasi dependensi.

- **Windows:**
  ```bash
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

**3. Install Dependensi**
Pastikan Anda sudah berada di dalam virtual environment yang aktif, lalu jalankan:

```bash
pip install -r requirements.txt
```

Perintah ini akan menginstall semua library yang dibutuhkan oleh bot.

**4. Konfigurasi Token Bot**

- Salin atau ganti nama file `.env.example` (jika ada) menjadi `.env`. Jika tidak ada, buat file baru bernama `.env`.
- Buka file `.env` dan masukkan token bot Telegram Anda.
  ```
  TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  ```
  > **Penting:** Dapatkan token Anda dari [@BotFather](https://t.me/BotFather) di Telegram. Jangan pernah membagikan token ini kepada siapa pun.

## 🚀 Menjalankan Bot

Setelah semua langkah instalasi selesai, jalankan bot dengan perintah:

```bash
python main.py
```

Jika tidak ada error, bot Anda sekarang aktif dan siap menerima pesan di Telegram.

## 🤖 Cara Menggunakan

1.  **Kirim Gambar:** Buka chat dengan bot Anda di Telegram dan kirimkan gambar apa pun yang ingin Anda proses.
2.  **Terima Hasil:** Bot akan memproses gambar tersebut dan mengirimkan kembali versi dengan latar belakang transparan (format PNG).
3.  **(Opsional) Ganti Latar:** Balas atau kirim pesan baru dengan perintah `/bg [warna]`.
    - Contoh penggunaan nama warna: `/bg blue`
    - Contoh penggunaan kode hex: `/bg #282c34`
4.  Bot akan mengirimkan gambar Anda dengan warna latar yang baru. Proses ini bisa diulangi dengan warna berbeda selama Anda tidak mengirim gambar baru. Jika Anda mengirim gambar baru, gambar itulah yang akan menjadi target untuk perintah `/bg` selanjutnya.
