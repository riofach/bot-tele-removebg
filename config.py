"""
Centralized configuration for Bot Telegram and API.
Professional configuration management with validation.
"""

import os
import json
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""

    pass


def get_list_from_env(key: str, default: List[str]) -> List[str]:
    """Parse list from environment variable with fallback."""
    env_value = os.getenv(key)
    if not env_value:
        return default

    try:
        return json.loads(env_value)
    except json.JSONDecodeError:
        # Fallback: split by comma
        return [item.strip() for item in env_value.split(",") if item.strip()]


# ===== TELEGRAM BOT CONFIGURATION =====
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")

# ===== API CONFIGURATION =====
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
API_KEY: Optional[str] = os.getenv("API_KEY")

# Rate Limiting
RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# File Upload Configuration
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_FILE_TYPES: List[str] = get_list_from_env(
    "ALLOWED_FILE_TYPES", ["image/jpeg", "image/png", "image/jpg"]
)

# CORS Configuration
CORS_ORIGINS: List[str] = get_list_from_env("CORS_ORIGINS", ["http://localhost:3000"])


def validate_telegram_config() -> None:
    """Validate Telegram bot configuration."""
    if not TELEGRAM_BOT_TOKEN:
        raise ConfigurationError(
            "TELEGRAM_BOT_TOKEN not found! Please check your .env file."
        )


def validate_api_config() -> None:
    """Validate API configuration."""
    if not (1 <= API_PORT <= 65535):
        raise ConfigurationError(f"Invalid API_PORT: {API_PORT}")

    if MAX_FILE_SIZE_MB <= 0:
        raise ConfigurationError(f"Invalid MAX_FILE_SIZE_MB: {MAX_FILE_SIZE_MB}")

    if RATE_LIMIT_PER_MINUTE <= 0:
        raise ConfigurationError(
            f"Invalid RATE_LIMIT_PER_MINUTE: {RATE_LIMIT_PER_MINUTE}"
        )


# Validate configurations on import
try:
    validate_api_config()
except ConfigurationError as e:
    print(f"⚠️  API Configuration Warning: {e}")

# Only validate Telegram config if token is expected
if os.getenv("REQUIRE_TELEGRAM_TOKEN", "false").lower() == "true":
    try:
        validate_telegram_config()
    except ConfigurationError as e:
        print(f"⚠️  Telegram Configuration Warning: {e}")
if API_KEY and len(API_KEY) < 32:
    raise ValueError(
        "API_KEY terlalu pendek! Gunakan minimal 32 karakter. "
        'Generate dengan: python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )
