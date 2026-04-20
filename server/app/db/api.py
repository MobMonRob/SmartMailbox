import os
import sqlite3

from server.app.db.model import (
    CompleteRecipientData,
    create_complete_recipient_data,
    Recipient,
    Household,
)


class Database:
    _instance = None
    con = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "database.db")

            cls.con = sqlite3.connect(db_path)

        return cls._instance

    def __del__(self):
        if self.con:
            self.con.close()


db: Database = Database()


def get_prompt() -> str:
    return db.con.execute(
        "select prompt from prompts where model = ?", ["Qwen3"]
    ).fetchone()["prompt"]


def get_recipients_data(household_id: int) -> list[CompleteRecipientData]:
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


def get_all_recipients(household_id: int) -> list[Recipient]:
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


def get_recipient_email(recipient_id: int) -> str:
    """
    Returns the email of the recipient with the given id.

    :param recipient_id: The id of the recipient.
    :return: The recipients email.
    """

    recipient = db.con.execute(
        "select * from recipients where recipients.id = ?", [recipient_id]
    ).fetchone()

    return recipient["email"]
