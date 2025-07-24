"""
File untuk konfigurasi terpusat untuk Bot Telegram dan API.
"""

import os
import json
from typing import List
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

# ===== TELEGRAM BOT CONFIGURATION =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN tidak ditemukan! Mohon periksa file .env Anda."
    )

# ===== API CONFIGURATION =====
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_KEY = os.getenv("API_KEY")

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# File Upload Limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Parse allowed file types from string to list
ALLOWED_FILE_TYPES_STR = os.getenv(
    "ALLOWED_FILE_TYPES", '["image/jpeg", "image/png", "image/jpg"]'
)
try:
    ALLOWED_FILE_TYPES: List[str] = json.loads(ALLOWED_FILE_TYPES_STR)
except json.JSONDecodeError:
    ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"]

# Parse CORS origins from string to list
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')
try:
    CORS_ORIGINS: List[str] = json.loads(CORS_ORIGINS_STR)
except json.JSONDecodeError:
    # Fallback: split by comma if JSON parsing fails
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Validate API configuration if API_KEY is provided
if API_KEY and len(API_KEY) < 32:
    raise ValueError(
        "API_KEY terlalu pendek! Gunakan minimal 32 karakter. "
        'Generate dengan: python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )
