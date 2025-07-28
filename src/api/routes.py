"""
FastAPI Routes - Main API endpoints for Background Remover
Professional implementation with clean architecture
"""

import time
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import FileResponse

from src.api.models import (
    RemoveBackgroundResponse,
    PasFotoResponse,
    BackgroundColor,
    PasFotoSize,
    BaseResponse,
)
from src.api.middleware import RateLimiter, APIKeyValidator
from src.api.utils import FileValidator, TempFileManager, ResponseBuilder
from src.core.remover import (
    remove_background,
    apply_solid_background,
    resize_pas_foto,
    create_a4_pdf_sheet,
)
import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api", tags=["Background Remover"])

# Initialize components (Dependency Injection pattern)
rate_limiter = RateLimiter()
temp_manager = TempFileManager()
response_builder = ResponseBuilder()


async def verify_api_key(request: Request) -> bool:
    """Dependency for API key validation"""
    if not config.API_KEY:
        return True  # Allow if no API key configured

    auth_header = request.headers.get("Authorization")
    provided_key = APIKeyValidator.extract_key_from_header(auth_header)

    if not APIKeyValidator.validate_key(provided_key, config.API_KEY):
        raise HTTPException(
            status_code=401,
            detail=response_builder.error_response(
                "Invalid or missing API key",
                "INVALID_API_KEY",
                {"required_format": "Authorization: Bearer YOUR_API_KEY"},
            ),
        )
    return True


async def check_rate_limit(request: Request) -> bool:
    """Dependency for rate limiting"""
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining_requests(client_ip)
        reset_time = rate_limiter.get_reset_time(client_ip)

        raise HTTPException(
            status_code=429,
            detail=response_builder.error_response(
                "Rate limit exceeded",
                "RATE_LIMIT_EXCEEDED",
                {
                    "remaining_requests": remaining,
                    "reset_time": reset_time.isoformat() if reset_time else None,
                    "limit_per_minute": config.RATE_LIMIT_PER_MINUTE,
                },
            ),
        )
    return True


@router.get("/health", response_model=BaseResponse)
async def health_check():
    """
    Health check endpoint - No authentication required
    For monitoring and debugging
    """
    return response_builder.success_response(
        "Background Remover API is healthy",
        {
            "service": "background-remover-api",
            "version": "1.0.0",
            "status": "operational",
        },
    )


@router.post("/remove-background", response_model=RemoveBackgroundResponse)
async def remove_background_endpoint(
    request: Request,
    file: UploadFile = File(..., description="Image file to remove background from"),
    background_color: Optional[str] = Form(
        None,
        description="Optional background color (hex code like #ff0000 or color name like 'red')",
    ),
    _auth: bool = Depends(verify_api_key),
    _rate_limit: bool = Depends(check_rate_limit),
):
    """
    Remove background from uploaded image

    - **file**: Image file (JPEG, PNG, JPG)
    - **background_color**: Optional background color to apply
    - Returns processed image URL or file
    """
    start_time = time.time()
    temp_files = []

    try:
        logger.info(f"Processing background removal request from {request.client.host}")

        # Validate uploaded file
        FileValidator.validate_file(
            file,
            file.file,
            max_size_mb=config.MAX_FILE_SIZE_MB,
            allowed_types=config.ALLOWED_FILE_TYPES,
        )

        # Read file content
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer

        # Process background removal
        logger.info("Starting background removal process")
        processed_image_bytes = remove_background(file_content)

        # Apply background color if specified
        if background_color:
            logger.info(f"Applying background color: {background_color}")
            processed_image_bytes = apply_solid_background(
                processed_image_bytes, background_color
            )

        # Save processed image to temporary file
        output_path = temp_manager.save_temp_file(
            processed_image_bytes, f"removed_bg_{int(time.time())}.png"
        )
        temp_files.append(output_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        logger.info(f"Background removal completed in {processing_time:.2f}s")

        # Return file response
        return FileResponse(
            path=output_path,
            media_type="image/png",
            filename=f"background_removed_{file.filename}",
            headers={
                "X-Processing-Time": str(processing_time),
                "X-Original-Filename": file.filename,
            },
        )

    except Exception as e:
        logger.error(f"Error in background removal: {str(e)}")
        processing_time = time.time() - start_time

        # Cleanup temp files on error
        temp_manager.cleanup_files(temp_files)

        raise HTTPException(
            status_code=500,
            detail=response_builder.error_response(
                "Failed to process background removal",
                "PROCESSING_ERROR",
                {"original_error": str(e), "processing_time": processing_time},
            ),
        )


@router.post("/pas-foto", response_model=PasFotoResponse)
async def create_pas_foto_endpoint(
    request: Request,
    file: UploadFile = File(
        ..., description="Image file to create passport photo from"
    ),
    background_color: BackgroundColor = Form(
        BackgroundColor.WHITE, description="Background color for passport photo"
    ),
    size: PasFotoSize = Form(PasFotoSize.SIZE_3X4, description="Passport photo size"),
    pdf_count: Optional[int] = Form(
        None,
        description="Number of photos in PDF layout (1-50). If not provided, returns single photo only",
        ge=1,
        le=50,
    ),
    _auth: bool = Depends(verify_api_key),
    _rate_limit: bool = Depends(check_rate_limit),
):
    """
    Create passport photo with specified size and background

    - **file**: Image file (JPEG, PNG, JPG)
    - **background_color**: Background color (white, red, blue, transparent)
    - **size**: Photo size (2x3, 3x4, 4x6, 2R, 3R, 4R, 5R)
    - **pdf_count**: Optional - number of photos in PDF layout
    - Returns single photo and/or PDF file
    """
    start_time = time.time()
    temp_files = []

    try:
        logger.info(f"Processing passport photo request from {request.client.host}")
        logger.info(
            f"Parameters: size={size}, background={background_color}, pdf_count={pdf_count}"
        )

        # Validate uploaded file
        FileValidator.validate_file(
            file,
            file.file,
            max_size_mb=config.MAX_FILE_SIZE_MB,
            allowed_types=config.ALLOWED_FILE_TYPES,
        )

        # Read file content
        file_content = await file.read()
        await file.seek(0)

        # Step 1: Remove background
        logger.info("Step 1: Removing background")
        no_bg_image_bytes = remove_background(file_content)

        # Step 2: Apply background color
        logger.info(f"Step 2: Applying {background_color} background")
        bg_applied_bytes = apply_solid_background(
            no_bg_image_bytes, background_color.value
        )

        # Step 3: Resize to passport photo size
        logger.info(f"Step 3: Resizing to {size}")
        resized_image_bytes = resize_pas_foto(bg_applied_bytes, size.value)

        # Save single photo
        single_photo_path = temp_manager.save_temp_file(
            resized_image_bytes, f"pas_foto_{size.value}_{int(time.time())}.png"
        )
        temp_files.append(single_photo_path)

        pdf_path = None

        # Step 4: Create PDF if requested
        if pdf_count and pdf_count > 1:
            logger.info(f"Step 4: Creating PDF with {pdf_count} photos")
            pdf_bytes = create_a4_pdf_sheet(resized_image_bytes, pdf_count, size.value)

            pdf_path = temp_manager.save_temp_file(
                pdf_bytes, f"pas_foto_{size.value}_{pdf_count}x_{int(time.time())}.pdf"
            )
            temp_files.append(pdf_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        logger.info(f"Passport photo creation completed in {processing_time:.2f}s")

        # Return appropriate response based on what was requested
        if pdf_path:
            # Return PDF if multiple photos requested
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf",
                filename=f"pas_foto_{size.value}_{pdf_count}x_{file.filename.split('.')[0]}.pdf",
                headers={
                    "X-Processing-Time": str(processing_time),
                    "X-Photo-Count": str(pdf_count),
                    "X-Photo-Size": size.value,
                    "X-Background-Color": background_color.value,
                },
            )
        else:
            # Return single photo
            return FileResponse(
                path=single_photo_path,
                media_type="image/png",
                filename=f"pas_foto_{size.value}_{file.filename}",
                headers={
                    "X-Processing-Time": str(processing_time),
                    "X-Photo-Size": size.value,
                    "X-Background-Color": background_color.value,
                },
            )

    except Exception as e:
        logger.error(f"Error in passport photo creation: {str(e)}")
        processing_time = time.time() - start_time

        # Cleanup temp files on error
        temp_manager.cleanup_files(temp_files)

        raise HTTPException(
            status_code=500,
            detail=response_builder.error_response(
                "Failed to create passport photo",
                "PROCESSING_ERROR",
                {
                    "original_error": str(e),
                    "processing_time": processing_time,
                    "parameters": {
                        "size": size.value,
                        "background_color": background_color.value,
                        "pdf_count": pdf_count,
                    },
                },
            ),
        )
