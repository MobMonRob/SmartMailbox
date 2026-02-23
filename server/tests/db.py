import sqlite3
import os


class Database:
    _instance = None
    con = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "../app/db/database.db")

            cls.con = sqlite3.connect(db_path)

        return cls._instance

    def __del__(self):
        if self.con:
            self.con.close()


db = Database()


def get_image_path(letter_id: int, quality: str) -> str | None:
    """
    Returns the path of the letter in the specified quality.

    :param letter_id: The id of the letter the image belongs to.
    :param quality: The quality of the image. Valid values are: "PERFECT" | "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF".

    :return: The path to the image or None if the path was not found.
    """

    return db.con.execute(
        "select image_path from letter_quality where letter_id = ? and quality = ?",
        [letter_id, quality],
    ).fetchone()


def get_prompt(model_family: str) -> str:
    """
    Returns the prompt for the model family.

    :param model_family: The model family: 'Qwen3' | 'Llama'.
    :return: The prompt for the model family.
    """
    return db.con.execute()
