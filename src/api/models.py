"""
Pydantic models for API request/response validation.
Professional, type-safe, and reusable data models.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from enum import Enum
import re


# === SHARED VALIDATION UTILITIES ===
class ColorValidator:
    """
    Centralized color validation utility to eliminate code duplication.
    """

    VALID_COLORS = [
        "red",
        "blue",
        "green",
        "white",
        "black",
        "yellow",
        "orange",
        "purple",
        "pink",
        "gray",
        "grey",
        "brown",
    ]

    @staticmethod
    def validate_color(color_value) -> str:
        """
        Shared validation logic for background colors.

        Args:
            color_value: Color value to validate (str, enum, or None)

        Returns:
            Validated color string

        Raises:
            ValueError: If color is invalid
        """
        if color_value is None:
            return None

        # Handle enum types
        if hasattr(color_value, "value"):
            return color_value.value

        # Handle string types
        if isinstance(color_value, str):
            # Check hex format
            if color_value.startswith("#"):
                if not re.match(r"^#[0-9A-Fa-f]{6}$", color_value):
                    raise ValueError("Hex color harus dalam format #RRGGBB")
                return color_value

            # Check named colors
            if color_value.lower() not in ColorValidator.VALID_COLORS:
                raise ValueError("Invalid color. Use color name or hex code.")
            return color_value.lower()

        return color_value


class BackgroundColor(str, Enum):
    """Standard background color options."""

    RED = "red"
    BLUE = "blue"
    WHITE = "white"
    TRANSPARENT = "transparent"


class PasFotoSize(str, Enum):
    """Supported passport photo sizes."""

    SIZE_2X3 = "2x3"
    SIZE_3X4 = "3x4"
    SIZE_4X6 = "4x6"
    SIZE_2R = "2R"
    SIZE_3R = "3R"
    SIZE_4R = "4R"
    SIZE_5R = "5R"


class BaseResponse(BaseModel):
    """Base response model yang dapat digunakan kembali."""

    success: bool
    message: str
    processing_time: Optional[float] = None

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "processing_time": 2.34,
            }
        }


class RemoveBackgroundRequest(BaseModel):
    """Request model untuk remove background endpoint."""

    background_color: Optional[str] = Field(
        None, description="Background color (nama warna atau hex code)", example="white"
    )

    @validator("background_color")
    def validate_background_color(cls, v):
        """Validasi format warna background menggunakan shared validator."""
        return ColorValidator.validate_color(v)


class RemoveBackgroundResponse(BaseResponse):
    """Response model untuk remove background endpoint."""

    image_url: Optional[str] = Field(
        None,
        description="URL gambar hasil processing",
        example="/static/processed/image_12345.png",
    )
    original_size: Optional[dict] = Field(
        None, description="Ukuran gambar asli", example={"width": 1920, "height": 1080}
    )
    processed_size: Optional[dict] = Field(
        None, description="Ukuran gambar hasil", example={"width": 1920, "height": 1080}
    )


class PasFotoRequest(BaseModel):
    """Request model untuk pas foto endpoint."""

    background_color: Optional[Union[BackgroundColor, str]] = Field(
        BackgroundColor.WHITE, description="Warna background (enum atau hex code)"
    )
    size: PasFotoSize = Field(PasFotoSize.SIZE_3X4, description="Ukuran pas foto")
    pdf_count: Optional[int] = Field(
        1, ge=1, le=50, description="Jumlah foto dalam PDF (1-50)"
    )

    @validator("background_color")
    def validate_background_color(cls, v):
        """Validasi background color menggunakan shared validator."""
        return ColorValidator.validate_color(v)


class PasFotoResponse(BaseResponse):
    """Response model untuk pas foto endpoint."""

    single_photo_url: Optional[str] = Field(
        None,
        description="URL foto tunggal",
        example="/static/processed/pasfoto_12345.png",
    )
    pdf_url: Optional[str] = Field(
        None, description="URL file PDF", example="/static/processed/pasfoto_12345.pdf"
    )
    photo_info: Optional[dict] = Field(
        None,
        description="Informasi foto",
        example={
            "size": "3x4",
            "background_color": "white",
            "pdf_count": 8,
            "dimensions": {"width": 330, "height": 450},
        },
    )


class HealthResponse(BaseModel):
    """Response model untuk health check endpoint."""

    status: str = Field("healthy", description="Status aplikasi")
    service: str = Field("background-remover-api", description="Nama service")
    version: str = Field("1.0.0", description="Versi API")
    timestamp: Optional[str] = Field(None, description="Timestamp check")


class ErrorResponse(BaseModel):
    """Response model untuk error handling."""

    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[dict] = Field(None, description="Error details")

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "success": False,
                "error": "File type not supported",
                "error_code": "INVALID_FILE_TYPE",
                "details": {"allowed_types": ["image/jpeg", "image/png", "image/jpg"]},
            }
        }


class FileValidationError(BaseModel):
    """Model untuk file validation errors."""

    field: str
    message: str
    file_info: Optional[dict] = None
