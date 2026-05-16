import logging
import io
import zipfile
import os
from .logger import setup_logging
from .model_tests_framework import run_tests

import smtplib
from email.message import EmailMessage
import traceback

setup_logging()

logger = logging.getLogger()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for STARTTLS
SENDER_EMAIL = "TODO"
SENDER_PASSWORD = "TODO"
RECIPIENT_EMAILS = []
DB_PATH = "app/db/database.db"


def send_email(subject: str, body: str, err: str = ""):
    logger.info(f"Sending {'Error' if err else 'Result'} email")
    msg = EmailMessage()
    msg.set_content(body + err)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENT_EMAILS)

    try:
        if os.path.exists(DB_PATH):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(DB_PATH, arcname="database.db")

            msg.add_attachment(
                zip_buffer.getvalue(),
                maintype="application",
                subtype="zip",
                filename="database.zip",
            )
            logger.info("Database zipped and attached.")
        else:
            logger.warning("Database file not found, skipping attachment.")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            logger.info(f"{err if err else 'Result'} email sent successfully!")
    except Exception as e:
        logger.error(f"Error while sending email: {e}")


def main():
    for model in [
        "qwen3.5:2b",
        "qwen3.5:4b",
        "qwen3.5:9b",
        "qwen3.5:27b",
        "qwen3.5:35b",
        "qwen3.5:122b",
        "llama3.3:70b",
        "llama3.2:1b",
        "llama3.2:3b",
    ]:
        logger.info(f"Testing model {model}")
        try:
            run_tests(model)
        except Exception as e:
            trace = traceback.format_exc()
            send_email(
                f"ERROR: Error while running model test for {model}",
                f"Error: {e}\n\n",
                trace,
            )
            logger.error(f"Error while running model test for {model}: {e}\n{trace}")
            logger.info("Continuing with next model")
            continue

        send_email(
            f"COMPLETED: Model test completed for {model}",
            f"Model test completed for {model} without exception.",
        )


if __name__ == "__main__":
    main()
