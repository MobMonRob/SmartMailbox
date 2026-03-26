import os.path
from typing import List, Tuple

from ollama import ChatResponse
import ollama

from .db.api import (
    get_image_path_and_id,
    get_all_recipients,
    get_household,
    create_model,
    get_test_cases,
    store_test_result,
    get_solution_recipient_ids,
    create_model_test,
    get_image_id,
)

from .db.model import (
    Model,
    ImageSelection,
    ImageQuality,
    ModelFamily,
    TestCase,
    Timings,
    CompleteRecipientData,
    create_complete_recipient_data,
    TestResult,
    ModelResponse,
    ModelAnswerCheck,
)

from . import qwen3, tesseract_llama

import logging

logger = logging.getLogger(__name__)


def run_tests(model_name: str, tests: set[int] | None = None):
    logger.info("Running tests ...")

    model = create_model(model_name)

    logger.info("Checking model availability ...")

    available_models = [model.model for model in ollama.list()["models"]]
    if model_name not in available_models:
        logger.info(f"Pulling model {model_name} ...")
        ollama.pull(model_name)
    logger.info("Model is available")

    test_cases = get_test_cases()

    logger.info(f"Found {len(test_cases)} test cases")

    # filter out unwanted tests
    if tests:
        test_cases = [test_case for idx, test_case in enumerate(test_cases) if idx in tests]

    logger.info(f"Running {len(test_cases)} test cases for model {model.name} ...")
    for test_case in test_cases:
        image_paths, image_ids = get_image_paths_and_ids(test_case.letter_id, test_case.image_selection)
        result = run_test_case(model, test_case, image_paths)

        if not result:
            continue

        response, timings, extracted_text = result

        response_message = response.message.content

        assert response_message is not None

        model_answer_check = check_response(response_message, test_case, image_ids)

        model_test_id = create_model_test(model, test_case)

        test_result = TestResult(
            time=timings.time,
            tesseract_time=timings.tesseract_time,
            llama_time=timings.llama_time,
            match_found=model_answer_check.match_found,
            correct_recipient_ids=model_answer_check.correct_recipient_ids,
            correct_image_id=model_answer_check.correct_image_id,
            model_test_id=model_test_id,
            complete_response=response_message,
            extracted_text=extracted_text,
            error_msg=model_answer_check.error_msg,
        )

        store_test_result(test_result)

    logger.info("DONE")


def run_test_case(model: Model, test_case: TestCase, image_paths: List[str]) -> Tuple[ChatResponse, Timings, str] | None:
    """
    Runs a test case for a given model.

    :param model: The model to test.
    :param test_case: The test case to use.
    :param image_paths: The paths to the images for the test case.
    :return: The response from the model and the timings.
    """
    logger.info(f"Running test case {test_case.id}")
    recipients_data = get_recipients_data(test_case.household_id)

    logger.info("Running test ...")
    match model.family:
        case ModelFamily.Qwen3:
            answer, timings = qwen3.test(image_paths, recipients_data, model.name)
            return answer, timings, ""
        case ModelFamily.Llama:
            return tesseract_llama.test(image_paths, recipients_data, model.name)


def get_image_paths_and_ids(letter_id: int, selection: ImageSelection) -> Tuple[List[str],List[int]]:
    """
    Returns a list of Image paths for the given letter and selection.

    :param letter_id: The id of the letter.
    :param selection: The selection of images.
    :return: A list of image paths.
    """
    logger.info(f"Getting image paths for selection {selection}")

    paths = []
    ids = []
    match selection:
        case ImageSelection.ALL:
            for image_quality in ImageQuality:
                path, image_id = get_image_path_and_id(letter_id, image_quality)
                paths.append(os.path.abspath(path))
                ids.append(image_id)
        case ImageSelection.PERFECT:
            path, image_id = get_image_path_and_id(letter_id, ImageQuality.PERFECT)
            paths.append(os.path.abspath(path))
            ids.append(image_id)
        case ImageSelection.SLIGHTLY_BLURRED:
            path, image_id = get_image_path_and_id(letter_id, ImageQuality.SLIGHTLY_BLURRED.SLIGHTLY_BLURRED)
            paths.append(os.path.abspath(path))
            ids.append(image_id)
        case ImageSelection.CUT_OFF:
            path, image_id = get_image_path_and_id(letter_id, ImageQuality.CUT_OFF)
            paths.append(os.path.abspath(path))
            ids.append(image_id)
        case ImageSelection.VERY_BLURRED:
            path, image_id = get_image_path_and_id(letter_id, ImageQuality.VERY_BLURRED)
            paths.append(os.path.abspath(path))
            ids.append(image_id)

    logger.info(f"Found {len(paths)} paths and IDs: {paths}, {ids}")
    return paths,ids


def get_recipients_data(household_id: int) -> List[CompleteRecipientData]:
    """
    Returns a list of recipients data for the given household.

    :param household_id: The id of the household.
    :return: A list of recipients data.
    """
    logger.info(f"Getting recipients data for household {household_id}")
    household = get_household(household_id)
    recipients = get_all_recipients(household_id)

    return [
        create_complete_recipient_data(recipient, household) for recipient in recipients
    ]


def check_response(model_response: str, test_case: TestCase, image_ids: List[int]) -> ModelAnswerCheck:
    """
    Checks the models response against the test case.

    :param model_response: The response from the model.
    :param test_case: The test case to use.
    :param image_ids: The IDs of the images.
    :return: ModelAnswerCheck.
    """
    logger.info("Checking response")

    try:
        logger.info("Parsing JSON")
        response = ModelResponse.model_validate_json(model_response)
    except Exception as e:
        return ModelAnswerCheck(
            match_found=False,
            correct_recipient_ids=False,
            correct_image_id=False,
            error_msg=f"JSON/Schema Error: {e}",
        )

    logger.info(f"Response: {response}")

    errors = []

    # Check Recipient IDs
    logger.info("Checking recipient IDs")
    recipient_err = check_recipient_ids(response.recipient_ids, test_case)
    if recipient_err:
        err = f"Error at correct recipients ID check: {recipient_err}"
        logger.info(err)
        errors.append(err)

    # Check Image ID
    logger.info("Checking best image ID")
    image_err = check_image_id(image_ids, test_case,response.best_image_id)
    if image_err:
        err = f"Error at correct image ID check: {image_err}"
        logger.info(err)
        errors.append(err)

    if not response.success and not response.fail_reason:
        err = "Model failed but provided no reason."
        logger.info(err)
        errors.append(err)

    return ModelAnswerCheck(
        match_found=response.success,
        correct_recipient_ids=not bool(recipient_err),
        correct_image_id=not bool(image_err),
        error_msg="\n".join(errors),
    )


def get_recipient_id_list_from_response(message: str) -> List[int]:
    """
    Get the recipient ids from the string array in the model's response.

    **Example**: '[1,2,3]' => [1, 2, 3]

    :param message: The response message
    :return: The list of recipient ids
    """

    return [
        int(recipient_id)
        for recipient_id in message.removeprefix("[").removesuffix("]").split(",")
    ]


def check_recipient_ids(recipient_ids: List[int], test_case: TestCase) -> str:
    """
    Check if the ids in the response matches the solution of the test case.

    :param recipient_ids: The list of id's to check.
    :param test_case: The test case.
    :return: Empty string if correct, else an error message.
    """
    correct_ids = get_solution_recipient_ids(test_case.id)

    if len(correct_ids) != len(recipient_ids):

        if len(recipient_ids) == 0:
            return f"No recipient IDs provided. Expected {len(correct_ids)} ({correct_ids})"
        else:
            return f"Expected {len(correct_ids)} recipient IDs ({correct_ids}), but got {len(recipient_ids)}: {recipient_ids}"

    recipient_ids.sort()
    correct_ids.sort()

    if recipient_ids == correct_ids:
        return ""

    return f"Provided recipient IDs do not match correct ids: {recipient_ids} != {correct_ids}"


def check_image_id(image_ids: List[int], test_case: TestCase, image_idx: int) -> str:
    """
    Check if the image idx in the response matches the solution of the test case.

    :param image_ids: The IDs of the images to check.
    :param test_case: The test case.
    :param image_idx: The idx of the image to check.
    :return: Empty string if correct, else an error message.
    """
    try:
        image_id = image_ids[image_idx]
    except IndexError:
        return f"Image idx is out of range of image paths: {image_idx} >= {len(image_ids)}"

    if test_case.image_selection == ImageSelection.ALL:
        # best image is image quality PERFECT
        correct_image_id = get_image_id(test_case.letter_id, ImageQuality.PERFECT)
    else:
        # best image is the image quality equal to test_case.image_selection
        quality = test_case.image_selection.value

        assert isinstance(quality, str)

        correct_image_id = get_image_id(test_case.letter_id, ImageQuality[quality])

    if image_id == correct_image_id:
        return ""

    return f"Provided image ID does not match correct image ID: {image_id} != {correct_image_id}"
