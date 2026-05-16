import io
import logging
import zipfile
from datetime import datetime
from typing import List
import requests
from config import cfg

logger = logging.getLogger(__name__)


def send_images_to_server(
    images: List[io.BytesIO], server_url: str, household_id: int
):
    """
    Sends in-memory images to a server in a zip archive.

    :param images: List of images to send.
    :param server_url: Server URL.
    :param household_id: Household ID.
    """
    logger.info(f"Creating zip archive for {len(images)} images.")

    archive = create_zip_archive(images)
    archive_name = (
        f"{cfg.archive_name_prefix}_{datetime.now()
        .strftime('%Y-%m-%d_%H:%M:%S')}.zip"
    )

    logger.info(f'Zip archive "{archive_name}" created.')
    logger.info(
        f'Sending images to server with URL "{server_url}" for household {household_id}.'
    )

    response = requests.post(
        server_url,
        files={"images": (archive_name, archive)},
        data={"household_id": household_id},
    )
    logger.info(
        f"Server response: {response.status_code, response.reason, response.text}"
    )


def create_zip_archive(buffers: List[io.BytesIO]) -> io.BytesIO:
    """
    Creates an in-memory zip archive of a list of byte buffers.

    :param images: List of buffers to zip.
    :return: In-memory zip archive.
    """
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip:
        for num, buffer in enumerate(buffers):
            image_name = f"{cfg.img_name_prefix}_{num}.{cfg.img_format}"

            zip.writestr(image_name, buffer.getvalue())
            logger.info(f"Added {image_name} to archive.")

            buffer.close()

    archive.seek(0)
    return archive
