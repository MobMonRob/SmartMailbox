import time
from typing import List, Tuple
import ollama
from ollama import ChatResponse

from server.app.db.model import CompleteRecipientData
from server.tests.db import get_prompt, Timings


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

    prompt = get_prompt(model_family="Qwen3")

    prompt += recipients_data

    start_time = time.time()

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt, "images": image_paths}],
    )

    end_time = time.time()

    timings = Timings()
    timings.time = end_time - start_time

    return response, timings
