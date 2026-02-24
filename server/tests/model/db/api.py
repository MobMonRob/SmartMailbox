import sqlite3
import os
from typing import List
from .model import Household, Recipient, ImageQuality, Model, ModelFamily, TestCase, TestResult


class Database:
    _instance = None
    con: sqlite3.Connection

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "../../../app/db/database.db")

            cls.con = sqlite3.connect(db_path)
            cls.con.row_factory = sqlite3.Row

        return cls._instance

    def __del__(self):
        if self.con:
            self.con.close()


db = Database()


def get_image_path(letter_id: int, quality: ImageQuality) -> str | None:
    """
    Returns the path of the letter in the specified quality.

    :param letter_id: The id of the letter the image belongs to.
    :param quality: The quality of the image. Valid values are: "PERFECT" | "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF".

    :return: The path to the image or None if the path was not found.
    """

    return db.con.execute(
        "select image_path from letter_quality where letter_id = ? and quality = ?",
        [letter_id, quality.value],
    ).fetchone()


def get_prompt(model_family: str) -> str:
    """
    Returns the prompt for the model family.

    :param model_family: The model family: 'Qwen3' | 'Llama'.
    :return: The prompt for the model family.
    """
    return db.con.execute(
        "select prompt from prompts where model = ?", [model_family]
    ).fetchone()


def get_household(household_id: int) -> Household:
    """
    Returns the household with the given id.

    :param household_id: The id of the household.
    :return: The household data.
    """

    household = db.con.execute(
        "select * from households where id = ?", [household_id]
    ).fetchone()

    return Household(
        id=household["id"],
        email=household["email"],
        country=household["country"],
        zipcode=household["zipcode"],
        city=household["city"],
        street=household["street"],
        house_number=household["house_number"],
    )


def get_all_recipients(household_id: int) -> List[Recipient]:
    """
    Returns all recipients for the given household.

    :param household_id: The id of the household.
    :return: A list of all the recipients.
    """

    recipients = db.con.execute(
        "select * from recipients where household = ?", [household_id]
    ).fetchall()

    return [
        Recipient(
            id=recipient["id"],
            firstname=recipient["firstname"],
            middlename=recipient["middlename"],
            surname=recipient["surname"],
            title=recipient["title"],
            email=recipient["email"],
            household=recipient["household"],
        )
        for recipient in recipients
    ]


def create_model(model_name: str) -> Model:
    """
    Creates a model object from a string.
    The family is derived from the model name.
    If the model already exists in the database it is reused,
    otherwise a new database entry is created.

    :param model_name: The model name.
    :return: The model object.
    """
    model = db.con.execute(
        "select * from models where name = ?", [model_name]
    ).fetchone()

    if model is None:
        lower_name = model_name.lower()
        if lower_name.startswith("qwen3"):
            model_family = ModelFamily.Qwen3
        elif lower_name.startswith("llama"):
            model_family = ModelFamily.Llama
        else:
            raise ValueError(f"Unknown model family: {model_name}")

        cursor = db.con.execute(
            "insert into models (name, family) values (?,?)",
            [model_name, model_family.value],
        )
        db.con.commit()

        model_id = cursor.lastrowid
        assert type(model_id) is int

        return Model(model_id, model_name, model_family)

    return Model(model["id"], model["name"], ModelFamily(model["family"]))


def get_test_cases() -> List[TestCase]:
    """
    Returns a list of all test cases.

    :return: list of test cases
    """
    test_cases = db.con.execute("select * from test_cases").fetchall()

    return [
        TestCase(
            id=test_case["id"],
            letter_id=test_case["letter_id"],
            image_selection=test_case["image_selection"],
            household_id=test_case["household_id"],
        )
        for test_case in test_cases
    ]


def store_test_result(test_result: TestResult):
    """
    Stores a test result in the database.

    :param test_result: The test result to store.
    """
    db.con.execute(
        "insert into model_test_results (time, tesseract_time, llama_time, match_found, correct_answer, test_id, complete_response) values (?,?,?,?,?,?,?)",[
            test_result.time,
            test_result.tesseract_time,
            test_result.llama_time,
            test_result.match_found,
            test_result.correct_answer,
            test_result.test_id,
            test_result.complete_response,
        ]
    )

def get_solution_recipient_ids(test_case_id: int) -> List[int]:
    """
    Get all correct recipient ids for a given test case.

    :param test_case_id: the id of the test case
    :return: a list of recipient ids
    """
    ids = db.con.execute(
        "select recipient_id from test_recipient_solutions where test_case_id = ?",
        [test_case_id]
    ).fetchall()

    return    [int(recipient_id) for recipient_id in ids]