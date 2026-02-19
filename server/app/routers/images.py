from fastapi import UploadFile, APIRouter, BackgroundTasks
import logging

from server.app.processing.uploaded_images import process_uploaded_images

logger = logging.getLogger(__name__)

router = APIRouter(
    tags= ["images"],
    responses={404: {"description": "Not found"}},
)

@router.post("/images")
def upload_images(images: UploadFile, background_tasks: BackgroundTasks):
    """
    Endpoint to receive a zip file containing images.
    Extracts the images and processes them.
    """
    return process_uploaded_images(images, background_tasks)
