# 🚀 Background Remover API - Server Running Guide

Setelah setup dan konfigurasi selesai, Anda memiliki **4 cara** untuk menjalankan services:

## 📝 **Cara Menjalankan Server**

### **1. Dual Service Mode - API + Bot (RECOMMENDED for PRODUCTION) ⭐**

```bash
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Jalankan kedua service bersamaan (API + Telegram Bot)
python run_dual_services.py

# Alternative options:
python run_dual_services.py --api-only    # Run API only
python run_dual_services.py --bot-only    # Run Bot only
```

**Features:**

- ✅ Professional service management
- ✅ Automatic restart on failure
- ✅ Graceful shutdown handling
- ✅ Comprehensive logging & monitoring
- ✅ Status reporting every 10 seconds

### **2. Enhanced Server Runner (RECOMMENDED for DEVELOPMENT) ⭐**

```bash
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Jalankan API server saja
python run_server.py

# Atau jalankan API + Bot menggunakan dual service
python run_server.py --with-bot
```

### **3. Menggunakan Uvicorn Command (CURRENT WORKING) ✅**

```bash
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Jalankan server dengan uvicorn
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### **3. Menggunakan api_server.py (ALTERNATIVE)**

```bash
# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Jalankan server dengan file alternative
python api_server.py
```

## 🔧 **Konfigurasi Server**

| Setting           | Value       | Description                            |
| ----------------- | ----------- | -------------------------------------- |
| **Host**          | `0.0.0.0`   | Accessible from all network interfaces |
| **Port**          | `8000`      | Default API port                       |
| **Reload**        | `True`      | Auto-reload on code changes            |
| **Rate Limit**    | `30/minute` | Request rate limiting                  |
| **Max File Size** | `10MB`      | Upload file size limit                 |
| **API Key**       | Required    | Bearer token authentication            |

## 📚 **Akses API**

- **Base URL**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🔐 **Authentication**

Semua API endpoints memerlukan API Key:

```http
Authorization: Bearer B_1ZoPBZ9dsUmtknKxJKqKp3U0n07IF3IIOfWOOl_h8
```

## 🎯 **Available Endpoints**

1. **Remove Background**: `POST /api/v1/remove-background`
2. **Passport Photo**: `POST /api/v1/passport-photo`
3. **Health Check**: `GET /` and `GET /health`

## 🤖 **Dual Service Mode Details**

Ketika menggunakan `run_dual_services.py`, Anda akan mendapatkan:

### **Real-time Monitoring:**

- Status report setiap 10 detik
- Automatic restart jika service crash (max 3 attempts)
- Graceful shutdown dengan Ctrl+C
- Comprehensive logging ke `dual_services.log`

### **Service Management:**

- **Telegram Bot**: Menangani user interactions via Telegram
- **FastAPI Server**: Menyediakan REST API untuk Next.js integration
- **Process Isolation**: Kedua service berjalan di process terpisah
- **Concurrent Operation**: Keduanya berjalan bersamaan tanpa blocking

### **Production Ready:**

- Environment validation sebelum start
- Signal handling untuk graceful shutdown
- Resource cleanup otomatis
- Error recovery mechanisms

## 💡 **Tips untuk Development**

- Gunakan `--reload` flag untuk auto-restart saat development
- Monitor logs untuk debugging
- Test endpoints di `/docs` untuk quick testing
- Konfigurasi CORS sudah diset untuk Next.js (`http://localhost:3000`)

## 🚨 **Troubleshooting**

Jika mengalami error:

1. Pastikan virtual environment aktif
2. Pastikan semua dependencies terinstall
3. Check file `.env` sudah benar
4. Gunakan uvicorn command sebagai fallback
