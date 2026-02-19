from fastapi import FastAPI
from .routers import images
import uvicorn
import logging

app = FastAPI()
app.include_router(images.router)


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(levelname)s" + reset + " (%(asctime)s - %(name)s): %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str,
        logging.INFO: green + format_str,
        logging.WARNING: yellow + format_str,
        logging.ERROR: red + format_str,
        logging.CRITICAL: bold_red + format_str,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Configure logging with the custom formatter
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())

logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
