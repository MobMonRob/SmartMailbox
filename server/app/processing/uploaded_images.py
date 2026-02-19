from typing import List

from fastapi import UploadFile, HTTPException
import zipfile
import io
import logging
import os

logger = logging.getLogger(__name__)

# TODO: Define uploaded JSON format (curr: { "images": <zipfile> })
def process_uploaded_images(images: UploadFile) -> dict:
    if not images.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a zip archive")

    try:
        # Read the file content into memory
        content = images.file.read()

        # Open the zip file from the bytes
        with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
            file_names = zip_ref.namelist()
            logger.info(f"Received zip file '{images.filename}' containing {len(file_names)} files.")

            # Directory to save extracted images TODO: Define temp directory for storing extracted images
            upload_dir = "uploaded_images"
            os.makedirs(upload_dir, exist_ok=True)

            processed_files: List[str] = []
            for file_name in file_names:
                # TODO: Maybe replace all this by just extracting the filename directly.
                #       As directories should not be part of the name anyway.
                #       Example: "abcd.png" => "abcd.png", "ab/cde.png" => "cde.png"
                #       This also prevents Zip Slip attacks

                # Prevent Zip Slip
                target_path = os.path.join(upload_dir, file_name)
                # Normalize path to resolve "../"
                target_path = os.path.normpath(target_path)

                # Skip path traversal attacks
                if not os.path.abspath(target_path).startswith(os.path.abspath(upload_dir)):
                    logger.warning(f"Skipping suspicious file: {file_name}")
                    continue

                # Extract manually to the sanitized path
                # Only extract if it's not a directory
                if not file_name.endswith('/'):
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(file_name) as source, open(target_path, "wb") as target:
                        target.write(source.read())

                    processed_files.append(file_name)
                    logger.info(f"Extracted: {file_name}")

            # TODO: Define returned JSON format
            return {
                "filename": images.filename,
                "message": "Images received and processed",
                "extracted_files": processed_files
            }

            # TODO: Process images with AI after returning

    except zipfile.BadZipFile:
        logger.error("Invalid zip file received.")
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
