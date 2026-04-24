from camera import take_pictures
import logging
from config import cfg
from client.src.image_processing import send_images_to_server

logger = logging.getLogger(__name__)

def main():
    log_file_name = "SmartMailbox.log"
    logging.basicConfig(
        filename=log_file_name,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    console_handler = logging.StreamHandler()
    logging.getLogger().addHandler(console_handler)

    logger.info("--- Smart Mailbox Application Started ---")

    images_buffers = take_pictures()

    if images_buffers:
        send_images_to_server(images_buffers, cfg.images_endpoint_url)
    else:
        logger.warning("No images were captured.")

    logger.info("--- Finished ---")


if __name__ == "__main__":
    main()
