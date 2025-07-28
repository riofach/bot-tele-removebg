"""
FastAPI Application - Main API server for Background Remover
Professional implementation with production-ready configuration
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router as api_router
from src.api.utils import ResponseBuilder
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize response builder
response_builder = ResponseBuilder()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Background Remover API Server...")
    logger.info(f"✅ API configured to run on {config.API_HOST}:{config.API_PORT}")
    logger.info(f"✅ Rate limit: {config.RATE_LIMIT_PER_MINUTE} requests/minute")
    logger.info(f"✅ Max file size: {config.MAX_FILE_SIZE_MB}MB")
    logger.info(f"✅ API Key required: {'Yes' if config.API_KEY else 'No'}")

    # Create directories if they don't exist
    os.makedirs("static/temp", exist_ok=True)
    os.makedirs("static/processed", exist_ok=True)
    logger.info("✅ Static directories created")

    yield

    # Shutdown
    logger.info("🔄 Shutting down Background Remover API Server...")
    # Cleanup tasks here if needed
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Background Remover API",
    description="""
    ## Professional Background Remover API
    
    This API provides endpoints for:
    - **Background Removal**: Remove backgrounds from images using AI
    - **Passport Photos**: Create professional passport photos with custom backgrounds and sizes
    
    ### Authentication
    - API Key required for all endpoints (except /health)
    - Use `Authorization: Bearer YOUR_API_KEY` header
    
    ### Rate Limiting
    - 30 requests per minute per IP address
    - Rate limit headers included in responses
    
    ### File Support
    - Supported formats: JPEG, PNG, JPG
    - Maximum file size: 10MB
    - High-quality output with transparency support
    """,
    version="1.0.0",
    contact={
        "name": "Background Remover API Team",
        "email": "support@backgroundremover.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)


# CORS Configuration
def setup_cors():
    """Setup CORS middleware for Next.js frontend"""
    cors_origins = config.CORS_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=[
            "X-Processing-Time",
            "X-Photo-Size",
            "X-Background-Color",
            "X-Photo-Count",
        ],
    )

    logger.info(f"✅ CORS configured for origins: {cors_origins}")


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers and process time tracking"""
    start_time = time.time()

    try:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"

        # Add processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        return response

    except Exception as e:
        # Log error and return proper error response
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s"
        )

        return JSONResponse(
            status_code=500,
            content=response_builder.error_response(
                "Internal server error",
                "INTERNAL_ERROR",
                {"processing_time": process_time},
            ),
        )


# Global Exception Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with consistent format"""
    return JSONResponse(
        status_code=404,
        content=response_builder.error_response(
            "Endpoint not found",
            "NOT_FOUND",
            {
                "path": str(request.url.path),
                "method": request.method,
                "available_endpoints": [
                    "GET /api/health",
                    "POST /api/remove-background",
                    "POST /api/pas-foto",
                    "GET /docs",
                    "GET /redoc",
                ],
            },
        ),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors with consistent format"""
    return JSONResponse(
        status_code=500,
        content=response_builder.error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"path": str(request.url.path), "method": request.method},
        ),
    )


# Setup CORS
setup_cors()

# Include routers
app.include_router(api_router)

# Note: Static files removed - using direct response instead of file serving


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return response_builder.success_response(
        "Background Remover API",
        {
            "service": "background-remover-api",
            "version": "1.0.0",
            "status": "operational",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_json": "/openapi.json",
            },
            "endpoints": {
                "health_check": "/api/health",
                "remove_background": "/api/remove-background",
                "passport_photo": "/api/pas-foto",
            },
            "authentication": {
                "required": bool(config.API_KEY),
                "method": "Bearer Token",
                "header": "Authorization: Bearer YOUR_API_KEY",
            },
            "rate_limiting": {
                "limit": f"{config.RATE_LIMIT_PER_MINUTE} requests per minute",
                "per": "IP address",
            },
            "file_support": {
                "max_size": f"{config.MAX_FILE_SIZE_MB}MB",
                "allowed_types": config.ALLOWED_FILE_TYPES,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Background Remover API Server...")

    uvicorn.run(
        "api_server:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        access_log=True,
        log_level="info",
    )
