import time
from typing import List, Tuple
import ollama
import pytesseract
from ollama import ChatResponse

from .db.model import Timings, CompleteRecipientData
from .db.api import get_prompt


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

    prompt += "\n".join(str(recipient) for recipient in recipients_data)

    prompt += f"\n{extracted_text}"

    llama_start_time = time.time()

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )

    llama_end_time = time.time()

    tesseract_time = tesseract_end_time - tesseract_start_time
    llama_time = llama_end_time - llama_start_time
    combined_time = tesseract_time + llama_time

    return response, Timings(combined_time, tesseract_time, llama_time)
