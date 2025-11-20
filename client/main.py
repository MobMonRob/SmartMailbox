from picamera2 import Picamera2


def main():
    picam2 = Picamera2()

    picam2.start()

    try:
        import time
        time.sleep(2)

        picam2.capture_file("test.jpg")
    finally:
        picam2.stop()

if __name__ == "__main__":
    main()
