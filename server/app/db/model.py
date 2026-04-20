from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel, model_validator


@dataclass
class Recipient:
    id: int
    firstname: str
    middlename: str
    surname: str
    title: str
    email: Optional[str]
    household: int


@dataclass
class Household:
    id: int
    email: str
    country: str
    zipcode: str
    city: str
    street: str
    house_number: str


@dataclass
class CompleteRecipientData:
    recipient_id: int
    household_id: int
    email: str
    firstname: str
    middlename: str
    surname: str
    title: str
    country: str
    zipcode: str
    city: str
    street: str
    house_number: str


@dataclass
class ModelResponse(BaseModel):
    success: bool
    recipient_ids: List[int]
    best_image_id: int
    fail_reason: str

    @model_validator(mode="after")
    def validate_consistency(self) -> "ModelResponse":
        if self.success and self.fail_reason:
            raise ValueError("Success is True but fail_reason is provided.")
        if not self.success and not self.fail_reason:
            raise ValueError("Success is False but fail_reason is empty.")
        return self


def create_complete_recipient_data(
    recipient: Recipient, household: Household
) -> CompleteRecipientData:
    return CompleteRecipientData(
        recipient_id=recipient.id,
        household_id=household.id,
        email=recipient.email if recipient.email else household.email,
        firstname=recipient.firstname,
        middlename=recipient.middlename,
        surname=recipient.surname,
        title=recipient.title,
        country=household.country,
        zipcode=household.zipcode,
        city=household.city,
        street=household.street,
        house_number=household.house_number,
    )
