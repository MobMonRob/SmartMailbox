from typing import List

from fastapi import UploadFile, HTTPException, Response, BackgroundTasks
import zipfile
import io
import logging
import os

from server.app.processing.process_images import process_images

logger = logging.getLogger(__name__)

# TODO: get this from config
images_base_path = "storage/uploads" 

def process_uploaded_images(images: UploadFile, background_tasks: BackgroundTasks):
    if not images.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a zip archive")
    try:
        # Read the file content into memory
        content = images.file.read()

        # Open the zip file from the bytes
        with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
            file_names = zip_ref.namelist()
            logger.info(f"Received zip file '{images.filename}' containing {len(file_names)} files.")

            # Directory to save extracted images
            upload_dir = os.path.join(images_base_path, secure_path(images.filename).replace(".zip", ""))
            os.makedirs(upload_dir, exist_ok=True)

            processed_files: List[str] = []
            for file_name in file_names:
                file_path = secure_path(file_name)

                # Only extract if it's not a directory
                if file_path == '':
                    logger.warning(f"File name is directory: {file_name}.")
                    continue

                # Extract manually to the sanitized path
                # os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # with zip_ref.open(file_name) as source, open(target_path, "wb") as target:
                #     target.write(source.read())

                processed_files.append(file_path)
                logger.info(f"Extracted: {file_name}")

            if len(processed_files) == 0:
                raise HTTPException(status_code=400, detail="No valid file was uploaded.")

            background_tasks.add_task(process_images(upload_dir))

            return Response(status_code=204)
    except zipfile.BadZipFile:
        logger.error("Invalid zip file received.")
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def secure_path(path: str) -> str:
    """
    Secure paths against zip slip attacks
    """
    return os.path.basename(path)