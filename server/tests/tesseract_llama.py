from typing import List
import ollama
import pytesseract
from ollama import ChatResponse

from server.app.db.model import CompleteRecipientData
from server.tests.db import get_prompt


def test(
    image_paths: List[str],
    recipients_data: List[CompleteRecipientData],
    model_name: str,
) -> ChatResponse:
    """
    :param image_paths: List of paths to images to test.
    :param recipients_data: List of Recipient objects.
    :param model_name: Name of the model to use, e.g. 'llama4'.

    :return: Response from the model.
    """

    extracted_text_list = [
        (image_idx, pytesseract.image_to_string(image_path, lang="de"))
        for image_idx, image_path in enumerate(image_paths)
    ]

    extracted_text = ""

    for image_idx, text in extracted_text_list:
        extracted_text += f"Image {image_idx}: {text}\n"

    prompt = get_prompt(model_family="Llama")

    prompt += f"{recipients_data}\n{extracted_text}"

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )

    return response
