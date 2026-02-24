from enum import Enum
from typing import List, Tuple

from ollama import ChatResponse

from db import get_image_path, get_prompt
from server.app.db.model import CompleteRecipientData, create_complete_recipient_data
from server.tests.db import (
    Model,
    ImageSelection,
    ImageQuality,
    ModelFamily,
    TestCase,
    get_household,
    get_all_recipients,
    Timings,
)
import qwen3
import tesseract_llama


def main():
    ...




def run_test_case(model: Model, test_case: TestCase) -> Tuple[ChatResponse, Timings]:
    """
    Runs a test case for a given model.

    :param model: The model to test.
    :param test_case: The test case to use.
    :return: The response from the model and the timings.
    """
    image_paths = get_image_paths(test_case.letter_id, test_case.image_selection)
    recipients_data = get_recipients_data(test_case.household_id)

    match model.family:
        case ModelFamily.Qwen3:
            return qwen3.test(image_paths, recipients_data, model.name)
        case ModelFamily.Llama:
            return tesseract_llama.test(image_paths, recipients_data, model.name)


def get_image_paths(letter_id: int, selection: ImageSelection) -> List[str]:
    """
    Returns a list of Image paths for the given letter and selection.

    :param letter_id: The id of the letter.
    :param selection: The selection of images.
    :return: A list of image paths.
    """
    paths = []
    match selection:
        case ImageSelection.ALL:
            for image_quality in ImageQuality:
                paths.append(get_image_path(letter_id, image_quality))
        case ImageSelection.PERFECT:
            paths.append(get_image_path(letter_id, ImageQuality.PERFECT))
        case ImageSelection.SLIGHTLY_BLURRED:
            paths.append(get_image_path(letter_id, ImageQuality.SLIGHTLY_BLURRED))
        case ImageSelection.FLASH_VISIBLE:
            paths.append(get_image_path(letter_id, ImageQuality.FLASH_VISIBLE))
        case ImageSelection.CUT_OFF:
            paths.append(get_image_path(letter_id, ImageQuality.CUT_OFF))
        case ImageSelection.VERY_BLURRED:
            paths.append(get_image_path(letter_id, ImageQuality.VERY_BLURRED))
    return paths


def get_recipients_data(household_id: int) -> List[CompleteRecipientData]:
    """
    Returns a list of recipients data for the given household.

    :param household_id: The id of the household.
    :return: A list of recipients data.
    """

    household = get_household(household_id)
    recipients = get_all_recipients(household_id)

    return [
        create_complete_recipient_data(recipient, household) for recipient in recipients
    ]
