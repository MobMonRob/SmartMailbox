import shutil

from urllib3.exceptions import RequestError, ResponseError

from server.app.db.api import get_prompt, get_household
from server.app.db.model import ModelResponse
from server.app.processing.process_response import (
    process_response,
    send_err_email,
    ProcessedResponse,
)
from server.tests.model.model_tests_framework import get_recipients_data
import ollama
import json
import os
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "qwen3.5:9b"


def process_images(dir_path: str, household_id: int):
    prompt = get_prompt()
    recipients_data = get_recipients_data(household_id)
    household = get_household(household_id)
    images = os.listdir(dir_path)
    prompt += json.dumps([recipient.__dict__ for recipient in recipients_data])

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt, "images": images}],
            format=ModelResponse.model_json_schema(),
        )
        process_response(response, images, household)
    except RequestError as err:
        err = f"Error during model request: {err}"
        logger.error(err)
        send_err_email(ProcessedResponse(None, None, err), images, household)
    except ResponseError as err:
        err = f"Error during model response: {err}"
        logger.error(err)
        send_err_email(ProcessedResponse(None, None, err), images, household)
    finally:
        shutil.rmtree(
            dir_path,
            onexc=lambda _, path, err: logger.error(
                f"Error while deleting directory {dir_path} at {path}: {err}"
            ),
        )
