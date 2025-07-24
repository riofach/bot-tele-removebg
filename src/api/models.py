"""
Pydantic models untuk API request/response validation.
Professional, reusable, dan type-safe models.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from enum import Enum
import re


class BackgroundColor(str, Enum):
    """Enum untuk pilihan warna background standar."""

    RED = "red"
    BLUE = "blue"
    WHITE = "white"
    TRANSPARENT = "transparent"


class PasFotoSize(str, Enum):
    """Enum untuk ukuran pas foto yang didukung."""

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
        """Validasi format warna background."""
        if v is None:
            return v

        # Check if it's a hex color
        if v.startswith("#"):
            if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                raise ValueError("Hex color harus dalam format #RRGGBB")
            return v

        # Check if it's a named color (basic validation)
        valid_colors = [
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
        if v.lower() not in valid_colors:
            raise ValueError(f"Warna tidak valid. Gunakan nama warna atau hex code.")

        return v.lower()


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
        """Validasi background color untuk pas foto."""
        if isinstance(v, BackgroundColor):
            return v.value

        if isinstance(v, str):
            # Same validation as RemoveBackgroundRequest
            if v.startswith("#"):
                if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                    raise ValueError("Hex color harus dalam format #RRGGBB")
                return v

            valid_colors = [
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
            if v.lower() not in valid_colors:
                raise ValueError(
                    f"Warna tidak valid. Gunakan nama warna atau hex code."
                )
            return v.lower()

        return v


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
