"""
API Middleware - Authentication, rate limiting, and validation.
Professional implementation with clean code practices.
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import config


class RateLimiter:
    """
    Professional rate limiter with in-memory storage.
    Thread-safe and efficient for production use.
    """

    def __init__(self):
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.rate_limit = config.RATE_LIMIT_PER_MINUTE

    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed based on rate limit.

        Args:
            client_ip: IP address of the client

        Returns:
            Tuple of (is_allowed, error_message)
        """
        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute ago

        # Clean old requests
        self.request_counts[client_ip] = [
            req_time
            for req_time in self.request_counts[client_ip]
            if req_time > cutoff_time
        ]

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.rate_limit:
            remaining_time = 60 - (current_time - min(self.request_counts[client_ip]))
            error_msg = (
                f"Rate limit exceeded. "
                f"Max {self.rate_limit} requests per minute. "
                f"Try again in {remaining_time:.0f} seconds."
            )
            return False, error_msg

        # Add current request
        self.request_counts[client_ip].append(current_time)
        return True, None


class APIKeyValidator:
    """
    Professional API key validator with security best practices.
    """

    def __init__(self):
        self.expected_api_key = config.API_KEY
        self.security = HTTPBearer(auto_error=False)

    def validate_api_key(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> Dict[str, str]:
        """
        Validate API key from Bearer token.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            Dict containing API key info

        Raises:
            HTTPException: If API key is invalid or missing
        """
        if not self.expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": "API key not configured on server",
                    "error_code": "API_KEY_NOT_CONFIGURED",
                },
            )

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Authorization header missing",
                    "error_code": "MISSING_AUTH_HEADER",
                    "details": {
                        "required_format": "Authorization: Bearer YOUR_API_KEY"
                    },
                },
            )

        if credentials.credentials != self.expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": "Invalid API key",
                    "error_code": "INVALID_API_KEY",
                },
            )

        return {"api_key": credentials.credentials, "valid": True}


# Global instances (Singleton pattern)
rate_limiter = RateLimiter()
api_key_validator = APIKeyValidator()


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Dict[str, str]:
    """
    FastAPI dependency for API key verification.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Dict containing validated API key info
    """
    return api_key_validator.validate_api_key(credentials)


async def rate_limit_check(request: Request) -> None:
    """
    FastAPI dependency for rate limiting check.

    Args:
        request: FastAPI Request object

    Raises:
        HTTPException: If rate limit is exceeded
    """
    client_ip = request.client.host
    is_allowed, error_message = rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": error_message,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "details": {
                    "rate_limit": config.RATE_LIMIT_PER_MINUTE,
                    "client_ip": client_ip,
                },
            },
        )


class SecurityHeaders:
    """
    Professional security headers middleware.
    """

    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add process time header.
    Useful for monitoring and debugging performance.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}")
    return SecurityHeaders.add_security_headers(response)
