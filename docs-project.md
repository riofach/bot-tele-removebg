# **Proyek: Bot Telegram Background Remover**

Dokumen ini menjelaskan rencana pengembangan untuk proyek Bot Telegram yang berfungsi sebagai penghapus latar belakang gambar.

Versi Dokumen: 1.0  
Tanggal: 1 Juli 2025

### **1\. Deskripsi Proyek**

Tujuan utama proyek ini adalah untuk membangun sebuah bot Telegram yang mampu menerima gambar dari pengguna, memproses gambar tersebut untuk menghilangkan latar belakangnya secara otomatis, dan mengirimkan kembali hasilnya kepada pengguna.

**Fitur Utama:**

- **Interaksi via Telegram:** Pengguna cukup mengirim gambar langsung ke bot.
- **Proses Otomatis:** Bot akan mendeteksi subjek/objek utama dalam gambar dan menghapus latarnya.
- **Mandiri (Standalone):** Sistem pemrosesan gambar berjalan di server kita sendiri menggunakan _library open-source_, tanpa bergantung pada API eksternal berbayar seperti remove.bg.
- **Output Berkualitas:** Hasil akhir adalah gambar dalam format .png dengan latar belakang transparan.

### **2\. Tech Stack**

Berikut adalah teknologi dan _library_ yang akan kita gunakan:

- **Bahasa Pemrograman:** **Python 3.8+**
  - _Alasan:_ Ekosistem yang sangat matang untuk AI/ML, pengembangan web, dan memiliki _library_ bot yang solid.
- **Framework Bot:** **python-telegram-bot**
  - _Alasan:_ _Library_ yang populer, stabil, terdokumentasi dengan baik, dan memudahkan interaksi dengan Telegram Bot API.
- **Core AI Library:** **rembg**
  - _Alasan:_ _Library_ _powerful_ yang menggunakan model AI (U-2-Net) untuk melakukan segmentasi gambar secara lokal. Ini adalah kunci agar proyek kita tidak bergantung pada layanan pihak ketiga.
- **Image Processing:** **Pillow**
  - _Alasan:_ _Library_ standar untuk membuka, memanipulasi, dan menyimpan berbagai format gambar di Python.
- **Environment Management:** **venv**
  - _Alasan:_ Praktik terbaik untuk mengisolasi _dependency_ proyek agar tidak tercampur dengan _library_ sistem dan proyek lainnya.

### **3\. Requirements (Kebutuhan)**

Hal-hal yang perlu disiapkan sebelum memulai pengembangan:

#### **Software**

- **Python** versi 3.8 atau yang lebih baru.
- **PIP** (Package Installer for Python).
- **Git** untuk manajemen versi (opsional tapi sangat direkomendasikan).
- **Teks Editor** atau **IDE** (misalnya: VS Code, PyCharm, Sublime Text).

#### **Kredensial**

- **Akun Telegram** yang aktif.
- **Telegram Bot Token:** Diperoleh dari BotFather di Telegram dengan langkah-langkah berikut:
  1. Buka aplikasi Telegram, cari user @BotFather (ada tanda centang biru).
  2. Mulai percakapan dengan mengetik /start.
  3. Kirim perintah /newbot untuk membuat bot baru.
  4. Ikuti instruksi untuk memberikan nama (display name) dan username untuk bot Anda.
  5. Setelah berhasil, BotFather akan memberikan token API. **Simpan token ini di tempat yang aman dan jangan pernah dibagikan ke publik.**

### **4\. Struktur Folder Proyek**

Kita akan mulai dengan struktur sederhana dan bisa dikembangkan menjadi lebih terstruktur seiring bertambahnya fitur.

#### **Tahap Awal (Struktur Minimal)**

Struktur ini cukup untuk memulai dan menjalankan fungsi dasar bot.

bot-tele-removebg/  
├── .venv/ \# Folder virtual environment (dibuat otomatis)  
├── .env \# Menyimpan token bot dan variabel rahasia lainnya  
├── .gitignore \# Daftar file/folder yang diabaikan oleh Git  
├── bot.py \# Kode utama bot kita  
└── requirements.txt \# Daftar semua library yang dibutuhkan

#### **Tahap Akhir/Skalabilitas (Struktur yang Lebih Baik)**

Jika proyek berkembang, kita bisa merapikannya seperti ini agar lebih mudah dikelola.

bot-tele-removebg/  
├── .venv/  
├── .env  
├── .gitignore  
├── config.py \# Pengaturan dan konfigurasi terpusat  
├── main.py \# Titik masuk utama untuk menjalankan bot  
├── requirements.txt  
└── src/ \# Folder utama untuk source code  
 ├── \_\_init\_\_.py  
 ├── bot/  
 │ ├── \_\_init\_\_.py  
 │ └── handlers.py \# Kumpulan fungsi yang menangani perintah/pesan  
 └── core/  
 ├── \_\_init\_\_.py  
 └── remover.py \# Logika inti untuk proses background removal

### **5\. Alur Kerja Sistem (System Workflow)**

Berikut adalah alur kerja sistem dari awal hingga akhir, langkah demi langkah:

1. **👨‍💻 User → 🤖 Bot:** Pengguna mengirim sebuah gambar (foto) ke chat bot Telegram kita.
2. **📡 Telegram API → 🖥️ Server Kita:** Server Telegram menerima gambar tersebut dan meneruskan informasinya (sebagai _update_) ke _script_ Python kita yang sedang berjalan.
3. **📥 Bot Script (Penerimaan):** _Handler_ di python-telegram-bot yang sudah kita siapkan akan mendeteksi bahwa _update_ yang masuk adalah sebuah gambar.
4. **⏳ Proses Download:** _Script_ kita akan mengunduh file gambar tersebut dari server Telegram. Untuk efisiensi, gambar akan diunduh langsung ke dalam memori (sebagai _byte stream_), bukan disimpan sebagai file fisik di server.
5. **🧠 Proses AI (rembg):** _Byte stream_ dari gambar asli akan dimasukkan ke dalam fungsi rembg.remove(). Di sinilah proses "ajaib" terjadi: model AI akan menganalisis gambar, memisahkan objek utama dari latar belakangnya.
6. **✅ Hasil Proses:** Fungsi rembg.remove() akan mengembalikan _byte stream_ baru, yaitu data gambar yang latar belakangnya sudah dibuat transparan (format PNG).
7. **📤 Bot Script (Pengiriman):** _Script_ kita mengambil hasil _byte stream_ tersebut.
8. **🖥️ Server Kita → 📡 Telegram API → 👨‍💻 User:** Bot mengirimkan kembali gambar hasil olahan tersebut kepada pengguna. Gambar dikirim sebagai "File" atau "Dokumen" untuk memastikan format PNG dan transparansinya tetap terjaga dengan sempurna.

Diagram Sederhana:  
User ↔️ Telegram ↔️ Server Python \[python-telegram-bot → rembg → Pillow\]
