import logging
import os.path
import smtplib
from dataclasses import dataclass
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ollama import ChatResponse
from pydantic import ValidationError

from server.app.db.api import get_recipient_email
from server.app.db.model import ModelResponse, Household

logger = logging.getLogger(__name__)


@dataclass
class ProcessedResponse:
    recipient_ids: Optional[list[int]]
    best_image_id: Optional[int]
    err: Optional[str]


def process_response(res: ChatResponse, images: list[str], household: Household):
    try:
        assert res.message.content
        response = ModelResponse.model_validate_json(res.message.content)
    except ValidationError as err:
        err = f"Error during model response validation: {err}"
        logger.error(err)
        return send_err_email(ProcessedResponse(None, None, err), images, household)

    if not response.success:
        err = f"Error during image processing:\n{response.fail_reason}"
        logger.error(err)
        return send_err_email(
            ProcessedResponse(None, response.best_image_id, err), images, household
        )

    return send_success_email(
        ProcessedResponse(response.recipient_ids, response.best_image_id, None), images
    )


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Standard port for STARTTLS
SENDER_EMAIL = "TODO"
SENDER_PASSWORD = "TODO"
SUBJECT = "You got new mail"


def send_err_email(
    processed_response: ProcessedResponse, images: list[str], household: Household
):
    logger.info("Sending error email.")

    assert isinstance(processed_response.err, str)
    assert processed_response.best_image_id

    send_email(
        processed_response.err,
        [household.email],
        images[processed_response.best_image_id],
    )


def send_success_email(processed_response: ProcessedResponse, images: list[str]):
    assert processed_response.recipient_ids is not None
    assert processed_response.best_image_id is not None

    logger.info("Sending success email.")
    recipient_emails = [
        get_recipient_email(recipient_id)
        for recipient_id in processed_response.recipient_ids
    ]

    send_email(
        "You got new mail. For a quick peek look at the attached image.",
        recipient_emails,
        images[processed_response.best_image_id],
    )


def send_email(body: str, recipient_emails: list[str], image_path: str):
    msg = MIMEMultipart()
    msg["Subject"] = SUBJECT
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(recipient_emails)
    msg.attach(MIMEText(body, "plain"))

    try:
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(image_path),
            )
            msg.attach(img)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email successfully sent to {recipient_emails}!")
    except Exception as err:
        logger.error(f"Error while sending email: {err}")
