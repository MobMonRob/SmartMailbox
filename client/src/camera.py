import io
from typing import List
from picamera2 import Picamera2
import logging
import time
from config import cfg

logger = logging.getLogger(__name__)


def take_pictures() -> List[io.BytesIO]:
    """
    Captures a burst of images directly to in-memory buffers.

    :param count: Number of images to take.
    :param warm_up_time: Seconds to wait for auto-exposure/white-balance.
    :return: List of BytesIO buffers containing JPEG data.
    """
    logger.info("Initiating camera.")
    picam2 = Picamera2()
    logger.info("Camera initiated.")

    picam2.start()
    logger.info("Camera started.")

    image_buffers: List[io.BytesIO] = []

    count = cfg.number_of_images

    try:
        logger.info(f"Waiting {cfg.warm_up_time_in_sec}s for warm-up...")
        time.sleep(cfg.warm_up_time_in_sec)

        logger.info(f"Starting capture of {count} images...")
        start_time = time.time()

        for i in range(count):
            stream = io.BytesIO()
            picam2.capture_file(stream, format=cfg.image_format)

            stream.seek(0)
            image_buffers.append(stream)

        duration = time.time() - start_time
        fps = count / duration

        logger.info(f"Captured {count} images in {duration:.2f}s ({fps:.2f} FPS).")
    except Exception as e:
        logger.error(f"Camera Error: {e}", exc_info=True)
    finally:
        picam2.stop()
        logger.info("Camera stopped.")

    return image_buffers
