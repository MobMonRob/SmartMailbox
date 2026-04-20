from fastapi import UploadFile, APIRouter, BackgroundTasks
import logging

from ..processing.process_zipfile import process_zipfile

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["images"],
    responses={404: {"description": "Not found"}},
)


@router.post("/images")
def upload_images(
    images: UploadFile, household_id: int, background_tasks: BackgroundTasks
):
    """
    Endpoint to receive a zip file containing images.
    Extracts the images and processes them.
    """
    return process_zipfile(images, household_id, background_tasks)
