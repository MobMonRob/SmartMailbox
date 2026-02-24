import sqlite3
import os
from typing import List
from .model import Household, Recipient, ImageQuality


class Database:
    _instance = None
    con: sqlite3.Connection

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "../../../app/db/database.db")

            cls.con = sqlite3.connect(db_path)

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
