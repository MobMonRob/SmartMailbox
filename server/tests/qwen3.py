from typing import List
from db.model import Recipient
import ollama
from ollama import ChatResponse

from server.tests.db import get_prompt


def test(
    image_paths: List[str], recipients_data: List[Recipient], model_name: str
) -> ChatResponse:
    """
    :param image_paths: List of paths to images to test.
    :param recipients_data: List of Recipient objects.
    :param model_name: Name of the model to use, e.g. 'qwen3-vl:8b'.

    :return: Response from the model.
    """

    prompt = get_prompt(model_family="Qwen3")

    prompt += recipients_data

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt, "images": image_paths}],
    )

    return response
