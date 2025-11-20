import io
import logging
import zipfile
from datetime import time
from typing import  List
import requests

logger = logging.getLogger(__name__)

def send_images_to_server(images: List[io.BytesIO], server_url: str):
    """
    Sends in-memory images to a server in a zip archive.

    :param images: List of images to send.
    :param server_url: Server URL.
    """
    logger.info(f"Creating zip archive for {len(images)} images.")

    archive = create_zip_archive(images)
    archive_name = f"Images_{time.strftime('%Y%m%d%H%M%S')}.zip"

    logger.info(f"Zip archive \"{archive_name}\" created.")
    logger.info(f"Sending images to server with URL \"{server_url}\".")

    response = requests.post(server_url, files={"images": (archive_name, archive)})
    logger.info(f"Server response: {response.status_code, response.reason, response.text}")


def create_zip_archive(buffers: List[io.BytesIO]) -> io.BytesIO:
    """
    Creates an in-memory zip archive of a list of byte buffers.

    :param images: List of buffers to zip.
    :return: In-memory zip archive.
    """
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zip:
        for num, buffer in enumerate(buffers):
            image_name = f"image_{num}.jpg"

            zip.writestr(image_name, buffer.getvalue())
            logger.info(f"Added {image_name} to archive.")

            buffer.close()

    archive.seek(0)
    return archive
