"""
FastAPI Background Remover Service - Main Application Entry Point

A professional API service for background removal and passport photo generation
with authentication, rate limiting, and comprehensive error handling.

Author: Bot Telegram Background Remover Team
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.api.middleware import RateLimiter
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Background Remover API Service")
    logger.info(f"📡 Server Host: {config.API_HOST}")
    logger.info(f"🔌 Server Port: {config.API_PORT}")
    logger.info(f"⚡ Rate Limit: {config.RATE_LIMIT_PER_MINUTE} requests/minute")
    logger.info(f"📁 Max File Size: {config.MAX_FILE_SIZE_MB}MB")
    logger.info(f"🎯 Allowed File Types: {', '.join(config.ALLOWED_FILE_TYPES)}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Background Remover API Service")


# Initialize FastAPI application
app = FastAPI(
    title="Background Remover API",
    description="""
    Professional Background Removal & Passport Photo Generation Service
    
    ## Features
    - 🎯 Remove image backgrounds with AI precision
    - 📸 Generate passport photos with custom dimensions
    - 🔐 Secure API key authentication
    - 🚦 Rate limiting protection
    - 📊 Comprehensive logging & monitoring
    - 🛡️ Input validation & error handling
    
    ## Security
    - API Key authentication required
    - Rate limiting: {rate_limit} requests per minute
    - File size limit: {max_size}MB
    - Supported formats: {formats}
    
    Built with ❤️ for Next.js teams
    """.format(
        rate_limit=config.RATE_LIMIT_PER_MINUTE,
        max_size=config.MAX_FILE_SIZE_MB,
        formats=", ".join(config.ALLOWED_FILE_TYPES),
    ),
    version="1.0.0",
    contact={
        "name": "Bot Telegram Background Remover Team",
        "email": "support@backgroundremover.com",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
)

# CORS Configuration for Next.js integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    from src.api.utils import ResponseBuilder

    response_builder = ResponseBuilder()
    return JSONResponse(
        status_code=400,
        content=response_builder.error_response(
            "Invalid input parameters", "VALIDATION_ERROR", {"error_details": str(exc)}
        ),
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc: FileNotFoundError):
    """Handle file not found errors"""
    from src.api.utils import ResponseBuilder

    response_builder = ResponseBuilder()
    return JSONResponse(
        status_code=404,
        content=response_builder.error_response(
            "Requested file not found", "FILE_NOT_FOUND", {"error_details": str(exc)}
        ),
    )


@app.get("/", tags=["Health Check"])
async def root():
    """
    Health check endpoint
    """
    return JSONResponse(
        content={
            "message": "🎯 Background Remover API is running!",
            "status": "healthy",
            "version": "1.0.0",
            "documentation": "/docs",
            "endpoints": {
                "remove_background": "/api/v1/remove-background",
                "passport_photo": "/api/v1/passport-photo",
            },
        },
        status_code=200,
    )


@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Detailed health check with system information
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "Background Remover API",
            "version": "1.0.0",
            "config": {
                "rate_limit": f"{config.RATE_LIMIT_PER_MINUTE}/minute",
                "max_file_size": f"{config.MAX_FILE_SIZE_MB}MB",
                "allowed_types": config.ALLOWED_FILE_TYPES,
            },
        },
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info",
    )
