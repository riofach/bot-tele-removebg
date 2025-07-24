"""
Utility functions untuk API operations.
Professional, reusable, dan well-documented utilities.
"""

import os
import uuid
import time
import aiofiles
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
import config

# Setup logging
logger = logging.getLogger(__name__)


class FileValidator:
    """
    Professional file validator dengan comprehensive checks.
    """

    @staticmethod
    def validate_file_type(file: UploadFile) -> bool:
        """
        Validate file type against allowed types.

        Args:
            file: FastAPI UploadFile object

        Returns:
            True if file type is valid

        Raises:
            HTTPException: If file type is not allowed
        """
        if file.content_type not in config.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": f"File type '{file.content_type}' not allowed",
                    "error_code": "INVALID_FILE_TYPE",
                    "details": {
                        "allowed_types": config.ALLOWED_FILE_TYPES,
                        "received_type": file.content_type,
                    },
                },
            )
        return True

    @staticmethod
    async def validate_file_size(file: UploadFile) -> bool:
        """
        Validate file size against maximum allowed size.

        Args:
            file: FastAPI UploadFile object

        Returns:
            True if file size is valid

        Raises:
            HTTPException: If file is too large
        """
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > config.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "success": False,
                    "error": f"File too large. Maximum size: {config.MAX_FILE_SIZE_MB}MB",
                    "error_code": "FILE_TOO_LARGE",
                    "details": {
                        "max_size_mb": config.MAX_FILE_SIZE_MB,
                        "received_size_mb": round(file_size / (1024 * 1024), 2),
                        "max_size_bytes": config.MAX_FILE_SIZE_BYTES,
                        "received_size_bytes": file_size,
                    },
                },
            )
        return True

    @staticmethod
    async def validate_upload_file(file: UploadFile) -> Dict[str, any]:
        """
        Comprehensive file validation.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Dict containing file info
        """
        # Validate file type
        FileValidator.validate_file_type(file)

        # Validate file size
        await FileValidator.validate_file_size(file)

        # Get file info
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "valid": True,
        }


class TempFileManager:
    """
    Professional temporary file manager dengan automatic cleanup.
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="bg_remover_"))
        self.created_files: List[Path] = []
        logger.info(f"TempFileManager initialized with directory: {self.temp_dir}")

    def generate_unique_filename(self, original_filename: str, suffix: str = "") -> str:
        """
        Generate unique filename dengan timestamp dan UUID.

        Args:
            original_filename: Original filename from upload
            suffix: Optional suffix untuk filename

        Returns:
            Unique filename
        """
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]

        if original_filename:
            name, ext = os.path.splitext(original_filename)
            clean_name = "".join(
                c for c in name if c.isalnum() or c in (" ", "-", "_")
            ).strip()[:20]
        else:
            clean_name = "upload"
            ext = ".png"

        return f"{clean_name}_{timestamp}_{unique_id}{suffix}{ext}"

    async def save_upload_file(
        self, file: UploadFile, suffix: str = ""
    ) -> Tuple[Path, Dict]:
        """
        Save uploaded file to temporary directory.

        Args:
            file: FastAPI UploadFile object
            suffix: Optional suffix untuk filename

        Returns:
            Tuple of (file_path, file_info)
        """
        # Validate file first
        file_info = await FileValidator.validate_upload_file(file)

        # Generate unique filename
        unique_filename = self.generate_unique_filename(file.filename, suffix)
        file_path = self.temp_dir / unique_filename

        # Save file
        try:
            async with aiofiles.open(file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            self.created_files.append(file_path)
            file_info.update(
                {"temp_path": str(file_path), "unique_filename": unique_filename}
            )

            logger.info(f"File saved to: {file_path}")
            return file_path, file_info

        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": "Failed to save uploaded file",
                    "error_code": "FILE_SAVE_ERROR",
                    "details": {"original_error": str(e)},
                },
            )

    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "temp_") -> Path:
        """
        Create empty temporary file.

        Args:
            suffix: File suffix/extension
            prefix: File prefix

        Returns:
            Path to created temporary file
        """
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}{timestamp}_{unique_id}{suffix}"
        file_path = self.temp_dir / filename

        # Create empty file
        file_path.touch()
        self.created_files.append(file_path)

        logger.debug(f"Created temp file: {file_path}")
        return file_path

    def cleanup_file(self, file_path: Path) -> bool:
        """
        Clean up specific file.

        Args:
            file_path: Path to file to cleanup

        Returns:
            True if successful
        """
        try:
            if file_path.exists():
                file_path.unlink()
                if file_path in self.created_files:
                    self.created_files.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
        return False

    def cleanup_all(self) -> int:
        """
        Clean up all created files and temp directory.

        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0

        for file_path in self.created_files.copy():
            if self.cleanup_file(file_path):
                cleaned_count += 1

        # Remove temp directory if empty
        try:
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                logger.info(f"Removed temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error removing temp directory: {e}")

        logger.info(f"Cleaned up {cleaned_count} temporary files")
        return cleaned_count

    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.cleanup_all()
        except Exception as e:
            logger.error(f"Error in TempFileManager destructor: {e}")


class ResponseBuilder:
    """
    Professional response builder untuk consistent API responses.
    """

    @staticmethod
    def success_response(
        message: str,
        data: Optional[Dict] = None,
        processing_time: Optional[float] = None,
    ) -> Dict:
        """
        Build success response.

        Args:
            message: Success message
            data: Optional data to include
            processing_time: Optional processing time

        Returns:
            Standardized success response
        """
        response = {"success": True, "message": message}

        if processing_time is not None:
            response["processing_time"] = round(processing_time, 4)

        if data:
            response.update(data)

        return response

    @staticmethod
    def error_response(
        error_message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
        status_code: int = 400,
    ) -> HTTPException:
        """
        Build error response.

        Args:
            error_message: Error message
            error_code: Optional error code
            details: Optional error details
            status_code: HTTP status code

        Returns:
            HTTPException with standardized error response
        """
        error_detail = {"success": False, "error": error_message}

        if error_code:
            error_detail["error_code"] = error_code

        if details:
            error_detail["details"] = details

        return HTTPException(status_code=status_code, detail=error_detail)


# Utility functions
def ensure_static_directories():
    """
    Ensure static directories exist for serving processed files.
    """
    directories = ["static/processed", "static/temp", "static/uploads"]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


def get_file_info(file_path: Path) -> Dict:
    """
    Get comprehensive file information.

    Args:
        file_path: Path to file

    Returns:
        Dict containing file information
    """
    if not file_path.exists():
        return {"exists": False}

    stat = file_path.stat()
    return {
        "exists": True,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created_time": stat.st_ctime,
        "modified_time": stat.st_mtime,
        "extension": file_path.suffix,
        "name": file_path.name,
        "stem": file_path.stem,
    }
