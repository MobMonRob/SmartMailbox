import io
import os
import shutil
import zipfile
import pytest
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the 'server' directory to sys.path so Python can find the 'app' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the router and dependency.
# Adjust these imports if your project structure differs slightly.
from app.routers.images import router

# Setup a test app specifically for this router
app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_upload_dir():
    """
    Fixture to clean up the 'uploaded_images' directory before and after each test.
    """
    upload_dir = "uploaded_images"
    # Cleanup before test
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    
    yield
    
    # Cleanup after test
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)

def create_zip_file(files: dict) -> io.BytesIO:
    """
    Helper to create a zip file in memory.
    files: dict where key is filename and value is content (bytes or str)
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for name, content in files.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            zip_file.writestr(name, content)
    zip_buffer.seek(0)
    return zip_buffer

def test_upload_valid_zip():
    """Test uploading a valid zip file with images."""
    files = {
        "image1.jpg": b"fake_image_content_1",
        "subdir/image2.png": b"fake_image_content_2"
    }
    zip_content = create_zip_file(files)
    
    response = client.post(
        "/images",
        files={"images": ("test_archive.zip", zip_content, "application/zip")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_archive.zip"
    assert "image1.jpg" in data["extracted_files"]
    assert "subdir/image2.png" in data["extracted_files"]
    
    # Verify files exist on disk
    assert os.path.exists(os.path.join("uploaded_images", "image1.jpg"))
    assert os.path.exists(os.path.join("uploaded_images", "subdir", "image2.png"))

def test_upload_invalid_extension():
    """Test uploading a file that is not a .zip."""
    response = client.post(
        "/images",
        files={"images": ("test.txt", io.BytesIO(b"text"), "text/plain")}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "File must be a zip archive"

def test_upload_corrupted_zip():
    """Test uploading a file with .zip extension but invalid content."""
    response = client.post(
        "/images",
        files={"images": ("corrupt.zip", io.BytesIO(b"not a zip"), "application/zip")}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid zip file"

def test_zip_slip_vulnerability():
    """
    Test that the server prevents 'Zip Slip' attacks.
    Files attempting to write outside the target directory should be skipped.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Safe file
        zip_file.writestr("safe.txt", b"safe")
        # Malicious file trying to go up two directories
        zip_file.writestr("../../evil.txt", b"evil")
    
    zip_buffer.seek(0)
    
    response = client.post(
        "/images",
        files={"images": ("attack.zip", zip_buffer, "application/zip")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 'safe.txt' should be processed
    assert "safe.txt" in data["extracted_files"]
    
    # '../../evil.txt' should NOT be processed/extracted
    assert "../../evil.txt" not in data["extracted_files"]
    
    # Verify evil.txt does not exist in the upload dir
    assert not os.path.exists(os.path.join("uploaded_images", "evil.txt"))