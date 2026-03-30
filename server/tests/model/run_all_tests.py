import logging

from .logger import setup_logging
from .model_tests_framework import run_tests

import smtplib
from email.message import EmailMessage
import traceback

setup_logging()

logger = logging.getLogger()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for STARTTLS
SENDER_EMAIL = "briefkaimusterkai@gmail.com"
SENDER_PASSWORD = "briefkai123123"
RECIPIENT_EMAILS = ["mschelkle05@web.de", "jasminfoerstel@gmail.com"]

def send_email(subject: str, body: str, err: str = ""):
    logger.info(f"Sending {err if err else "Result"} email")
    msg = EmailMessage()
    msg.set_content(body + err)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECIPIENT_EMAILS)

    try:
        with open("../../app/db/database.db", 'rb') as f:
            file_data = f.read()
            file_name = "database.db"

        msg.add_attachment(
            file_data,
            maintype='application',
            subtype='octet-stream',
            filename=file_name
        )

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            logger.info(f"{err if err else "Result" } email sent successfully!")
    except Exception as e:
        logger.error(f"Error while sending email: {e}")

def main():
    for model in ["qwen3.5:2b", "qwen3.5:4b", "qwen3.5:9b", "qwen3.5:27b", "qwen3.5:35b", "qwen3.5:122b", "llama4:scout", "llama3.2:1b", "llama3.2:3b"]:
        try:
            run_tests(model)
        except Exception as e:
            send_email(f"ERROR: Error while running model test for {model}", f"Error: {e}\n\n" , traceback.format_exc())
            return

        send_email(f"COMPLETED: Model test completed for {model}", f"Model test completed for {model} without exception.")

if __name__ == "__main__":
    main()