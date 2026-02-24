from typing import List, Tuple

from ollama import ChatResponse

from .db.api import get_image_path, get_all_recipients, get_household, create_model, get_test_cases, store_test_result, \
    get_solution_recipient_ids

from .db.model import (
    Model,
    ImageSelection,
    ImageQuality,
    ModelFamily,
    TestCase,
    Timings,
    CompleteRecipientData,
    create_complete_recipient_data, TestResult,
)

from . import qwen3, tesseract_llama


def run_tests(model_name: str):
    model = create_model(model_name)

    test_cases = get_test_cases()

    for test_case in test_cases:
        response, timings = run_test_case(model, test_case)

        match_found, correct_answer = check_response(response, test_case)

        test_result = TestResult(
            time=timings.time,
            tesseract_time=timings.tesseract_time,
            llama_time=timings.llama_time,
            match_found=match_found,
            correct_answer=correct_answer,
            test_id=test_case.id,
            complete_response=response.message.content,
        )

        store_test_result(test_result)


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

# TODO: improve this code to match the json response format of the model
def check_response(response: ChatResponse, test_case: TestCase) -> Tuple[bool, bool]:
    """
    Checks the models response against the test case.

    :param response: The response from the model.
    :param test_case: The test case to use.
    :return: Tuple of bools consisting of match_found and correct_answer.
    """
    message = response.message.content

    if message.startswith("SUCCESS"):
        match_found = True
        message = message.removeprefix("SUCCESS;")

        recipient_ids = get_recipient_id_list_from_response(message)

        if match_found and len(recipient_ids) == 0:
            raise Exception(f"Successful match but no recipient ids found {message}")

        correct_answer = match_response_against_solution(recipient_ids, test_case.id)

        return match_found, correct_answer

    if message.startswith("FAIL"):
        match_found = False

        correct_ids = get_solution_recipient_ids(test_case.id)
        correct_answer = len(correct_ids) == 0

        return match_found, correct_answer

    raise Exception(f"Invalid response format: {message}")


def get_recipient_id_list_from_response(message: str)-> List[int]:
    """
    Get the recipient ids from the string array in the models response.

    **Example**: '[1,2,3]' => [1, 2, 3]

    :param message: The response message
    :return: The list of recipient ids
    """

    return [int(recipient_id) for recipient_id in message.removeprefix("[").removesuffix("]").split(",")]

def match_response_against_solution(recipient_ids: List[int], test_case_id: int) -> bool:
    """
    Check if the ids in the response matches the solution.

    :param

    """
    correct_ids = get_solution_recipient_ids(test_case_id)

    if len(correct_ids) != len(recipient_ids):
        return  False

    recipient_ids.sort()
    correct_ids.sort()

    return recipient_ids == correct_ids




