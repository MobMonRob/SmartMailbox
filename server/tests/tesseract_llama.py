import time
from typing import List, Tuple
import ollama
import pytesseract
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
    :param model_name: Name of the model to use, e.g. 'llama4'.

    :return: Response from the model and the timings.
    """

    prompt = get_prompt(model_family="Llama")

    tesseract_start_time = time.time()

    extracted_text_list = [
        (image_idx, pytesseract.image_to_string(image_path, lang="de"))
        for image_idx, image_path in enumerate(image_paths)
    ]

    extracted_text = ""

    for image_idx, text in extracted_text_list:
        extracted_text += f"Image {image_idx}: {text}\n"

    tesseract_end_time = time.time()

    prompt += f"{recipients_data}\n{extracted_text}"

    llama_start_time = time.time()

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )

    llama_end_time = time.time()

    timings = Timings()
    timings.tesseract_time = tesseract_end_time - tesseract_start_time
    timings.llama_time = llama_end_time - llama_start_time
    timings.time = timings.tesseract_time + timings.llama_time

    return response, timings
