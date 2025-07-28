"""
Automated Test Suite for Background Remover API
Professional testing implementation with pytest and FastAPI TestClient
"""

import pytest
import os
import io
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import tempfile

# Import the FastAPI app
from api_server import app

# Create test client
client = TestClient(app)

# Test configuration
TEST_API_KEY = "test-api-key-12345"
INVALID_API_KEY = "invalid-key"


@pytest.fixture
def valid_headers():
    """Fixture for valid authentication headers"""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}


@pytest.fixture
def invalid_headers():
    """Fixture for invalid authentication headers"""
    return {"Authorization": f"Bearer {INVALID_API_KEY}"}


@pytest.fixture
def sample_image():
    """Fixture to create a sample test image"""
    # Create a simple test image
    img = Image.new("RGB", (300, 300), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def large_image():
    """Fixture to create a large test image for size limit testing"""
    # Create a large image (>10MB)
    img = Image.new("RGB", (5000, 5000), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=100)
    img_bytes.seek(0)
    return img_bytes


class TestHealthEndpoint:
    """Test cases for health check endpoint"""

    def test_health_check_success(self):
        """Test health endpoint returns success"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "operational" in response.json()["message"].lower()

    def test_health_check_no_auth_required(self):
        """Test health endpoint works without authentication"""
        response = client.get("/api/health")
        assert response.status_code == 200


class TestAuthentication:
    """Test cases for API authentication"""

    def test_valid_api_key_access(self, valid_headers, sample_image):
        """Test API access with valid API key"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files
        )
        assert response.status_code != 401  # Should not be unauthorized

    def test_invalid_api_key_rejection(self, invalid_headers, sample_image):
        """Test API rejects invalid API key"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        response = client.post(
            "/api/remove-background", headers=invalid_headers, files=files
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]["error"]

    def test_missing_api_key_rejection(self, sample_image):
        """Test API rejects requests without API key"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        response = client.post("/api/remove-background", files=files)
        assert (
            response.status_code == 403
        )  # FastAPI returns 403 for missing bearer token


class TestRemoveBackgroundEndpoint:
    """Test cases for remove background endpoint"""

    def test_remove_background_success(self, valid_headers, sample_image):
        """Test successful background removal"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files
        )

        # Should return success or actual file response
        assert response.status_code in [200, 201]

    def test_remove_background_with_color(self, valid_headers, sample_image):
        """Test background removal with color replacement"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        data = {"background_color": "white"}
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files, data=data
        )

        assert response.status_code in [200, 201]

    def test_invalid_file_type_rejection(self, valid_headers):
        """Test rejection of invalid file types"""
        # Create a text file instead of image
        text_content = b"This is not an image"
        files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files
        )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]["error"].lower()

    def test_large_file_rejection(self, valid_headers, large_image):
        """Test rejection of oversized files"""
        files = {"file": ("large.jpg", large_image, "image/jpeg")}
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files
        )

        assert response.status_code == 413  # Request Entity Too Large


class TestPasFotoEndpoint:
    """Test cases for pas foto endpoint"""

    def test_pas_foto_creation_success(self, valid_headers, sample_image):
        """Test successful pas foto creation"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        data = {"background_color": "white", "size": "3x4", "pdf_count": 1}
        response = client.post(
            "/api/pas-foto", headers=valid_headers, files=files, data=data
        )

        assert response.status_code in [200, 201]

    def test_pas_foto_with_pdf_output(self, valid_headers, sample_image):
        """Test pas foto with PDF output"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        data = {"background_color": "blue", "size": "3x4", "pdf_count": 6}
        response = client.post(
            "/api/pas-foto", headers=valid_headers, files=files, data=data
        )

        assert response.status_code in [200, 201]

    def test_invalid_size_parameter(self, valid_headers, sample_image):
        """Test pas foto with invalid size parameter"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        data = {"background_color": "white", "size": "invalid_size", "pdf_count": 1}
        response = client.post(
            "/api/pas-foto", headers=valid_headers, files=files, data=data
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_pdf_count(self, valid_headers, sample_image):
        """Test pas foto with invalid PDF count"""
        files = {"file": ("test.jpg", sample_image, "image/jpeg")}
        data = {
            "background_color": "white",
            "size": "3x4",
            "pdf_count": 100,  # Over the limit of 50
        }
        response = client.post(
            "/api/pas-foto", headers=valid_headers, files=files, data=data
        )

        assert response.status_code == 422  # Validation error


class TestRateLimiting:
    """Test cases for rate limiting functionality"""

    def test_rate_limit_enforcement(self, valid_headers):
        """Test that rate limiting is enforced"""
        # Make multiple requests quickly
        responses = []
        for i in range(35):  # Exceed the 30 requests/minute limit
            response = client.get("/api/health", headers=valid_headers)
            responses.append(response)

        # Should get some 429 responses
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests


class TestErrorHandling:
    """Test cases for error handling"""

    def test_404_for_invalid_endpoint(self):
        """Test 404 response for invalid endpoints"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self):
        """Test 405 response for wrong HTTP methods"""
        response = client.get("/api/remove-background")  # Should be POST
        assert response.status_code == 405


class TestCORS:
    """Test cases for CORS configuration"""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = client.get("/api/health")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers

    def test_preflight_request(self):
        """Test CORS preflight request handling"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        }
        response = client.options("/api/remove-background", headers=headers)

        assert response.status_code in [200, 204]


class TestPerformance:
    """Test cases for performance validation"""

    def test_response_time_baseline(self, valid_headers, sample_image):
        """Test that API responses are within acceptable time limits"""
        import time

        files = {"file": ("test.jpg", sample_image, "image/jpeg")}

        start_time = time.time()
        response = client.post(
            "/api/remove-background", headers=valid_headers, files=files
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Should respond within 30 seconds for small test image
        assert processing_time < 30.0

        # Check if processing time header is present
        if "X-Process-Time" in response.headers:
            api_processing_time = float(response.headers["X-Process-Time"])
            assert api_processing_time > 0


# Test configuration setup
def setup_test_environment():
    """Setup test environment with mock API key"""
    os.environ["API_KEY"] = TEST_API_KEY
    os.environ["RATE_LIMIT_PER_MINUTE"] = "30"
    os.environ["MAX_FILE_SIZE_MB"] = "10"


if __name__ == "__main__":
    # Setup test environment
    setup_test_environment()

    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
