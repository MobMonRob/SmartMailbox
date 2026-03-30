import json
import time
from typing import List, Tuple
import ollama
from ollama import ChatResponse

from .db.api import get_prompt
from .db.model import Timings, CompleteRecipientData, ModelFamily, ModelResponse
from .logger import logger

def test(
    image_paths: List[str],
    recipients_data: List[CompleteRecipientData],
    model_name: str,
) -> Tuple[ChatResponse, Timings]:
    """
    :param image_paths: List of paths to images to test.
    :param recipients_data: List of Recipient objects.
    :param model_name: Name of the model to use, e.g. 'qwen3-vl:8b'.

    :return: Response from the model and the timings.
    """
    logger.info(
        f"Testing {model_name} with images {image_paths} and recipient data {recipients_data}"
    )

    prompt = get_prompt(model_family=ModelFamily.Qwen3)

    prompt += json.dumps([recipient.__dict__ for recipient in recipients_data])

    logger.info(f"Running {model_name}")
    start_time = time.time()

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt, "images": image_paths}],
        format=ModelResponse.model_json_schema(),
    )

    end_time = time.time()

    logger.info("Finished run")

    elapsed_time = end_time - start_time

    logger.info(f"Elapsed time: {elapsed_time}")

    return response, Timings(elapsed_time)
