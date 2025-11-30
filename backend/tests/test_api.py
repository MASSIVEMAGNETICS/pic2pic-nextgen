"""
Tests for the FastAPI application and routes.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns correct data."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "deployment_tier" in data


class TestPresetsEndpoint:
    """Test presets endpoint."""

    def test_list_presets(self, client):
        """Test listing presets."""
        response = client.get("/api/v1/presets")
        assert response.status_code == 200

        presets = response.json()
        assert len(presets) >= 4

        # Check preset structure
        preset_names = [p["name"] for p in presets]
        assert "Enhance" in preset_names
        assert "Stylize" in preset_names


class TestUploadEndpoint:
    """Test upload endpoint."""

    def test_upload_invalid_file(self, client):
        """Test uploading non-image file."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
        assert response.status_code == 400

    def test_upload_valid_image(self, client):
        """Test uploading valid image."""
        # Minimal valid PNG
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x00, 0x00, 0x00, 0x00, 0x3A, 0x7E, 0x9B,
            0x55, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x60, 0x00, 0x00, 0x00,
            0x02, 0x00, 0x01, 0x73, 0x75, 0x01, 0x18, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])

        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.png", png_data, "image/png")}
        )
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"


class TestJobEndpoint:
    """Test job status endpoint."""

    def test_get_nonexistent_job(self, client):
        """Test getting status of non-existent job."""
        response = client.get("/api/v1/job/nonexistent-id")
        assert response.status_code == 404


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "pic2pic-nextgen"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestDevEndpoints:
    """Test dev mode endpoints."""

    def test_get_dev_parameters_without_flag(self, client):
        """Test getting dev parameters without dev flag."""
        response = client.get("/api/v1/dev/parameters")
        # In dev-alpha tier, should work
        assert response.status_code == 200

    def test_get_dev_parameters_with_flag(self, client):
        """Test getting dev parameters with dev flag."""
        response = client.get("/api/v1/dev/parameters?dev_mode=true")
        assert response.status_code == 200

        data = response.json()
        assert "tau_scale_1" in data
        assert "binding_temperature" in data
