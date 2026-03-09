# /// script
# dependencies = [
#   "picamera2"
# ]
# ///

import sys

from picamera2 import Picamera2

def take_picture(image_name: str):
    """
    Captures an images.

    :image_name: Name of the image.
    """
    print("Initiating camera.")
    picam2 = Picamera2()
    print("Camera initiated.")

    picam2.start()
    print("Camera started.")

    try:
        picam2.capture_file(f"images/{image_name}.png", format="PNG")
    except Exception as e:
        print(f"Camera Error: {e}")
    finally:
        picam2.stop()
        print("Camera stopped.")


if __name__ == '__main__':
    take_picture(sys.argv[1])