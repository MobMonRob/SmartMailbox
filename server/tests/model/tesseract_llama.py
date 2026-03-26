import time
from typing import List, Tuple
import ollama
import pytesseract
from PIL import Image, ImageFile
from ollama import ChatResponse

from .db.model import Timings, CompleteRecipientData, ModelFamily, ModelResponse
from .db.api import get_prompt
import logging
import json

logger = logging.getLogger(__name__)


def test(
    image_paths: List[str],
    recipients_data: List[CompleteRecipientData],
    model_name: str,
) -> Tuple[ChatResponse, Timings, str] | None:
    """
    :param image_paths: List of paths to images to test.
    :param recipients_data: List of Recipient objects.
    :param model_name: Name of the model to use, e.g. 'llama4'.

    :return: Response from the model, the timings and the extracted text.
    """
    logger.info(
        f"Testing {model_name} with images {image_paths} and recipient data {recipients_data}"
    )
    prompt = get_prompt(model_family=ModelFamily.Llama)

    logger.info("Running tesseract")
    tesseract_start_time = time.time()

    extracted_text_list = []


    for image_idx, image_path in enumerate(image_paths):
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        try:
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img, lang='deu')
                extracted_text_list.append((image_idx, text))
        except Exception  as e:
            logger.error(f"Could not open image {image_path}: {e}")
            return None

    extracted_text = ""

    for image_idx, text in extracted_text_list:
        extracted_text += f"Image {image_idx}: {text}\n"

    tesseract_end_time = time.time()

    logger.info("Finished run")
    logger.info(
        f"Elapsed time for tesseract: {tesseract_end_time - tesseract_start_time}"
    )

    prompt += json.dumps([recipient.__dict__ for recipient in recipients_data])

    prompt += f"\nExtracted texts (0-indexed):\n{extracted_text}"

    logger.info(f"Running {model_name}")

    llama_start_time = time.time()

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        format=ModelResponse.model_json_schema(),
    )

    llama_end_time = time.time()

    logger.info("Finished run")

    tesseract_time = tesseract_end_time - tesseract_start_time
    llama_time = llama_end_time - llama_start_time
    combined_time = tesseract_time + llama_time

    logger.info(f"Elapsed time for {model_name}: {llama_time}")
    logger.info(f"Elapsed time combined: {combined_time}")

    return response, Timings(combined_time, tesseract_time, llama_time), extracted_text
