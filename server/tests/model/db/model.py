from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, model_validator


class ImageSelection(Enum):
    ALL = "ALL"
    PERFECT = "PERFECT"
    SLIGHTLY_BLURRED = "SLIGHTLY_BLURRED"
    VERY_BLURRED = "VERY_BLURRED"
    CUT_OFF = "CUT_OFF"


class ImageQuality(Enum):
    PERFECT = "PERFECT"
    SLIGHTLY_BLURRED = "SLIGHTLY_BLURRED"
    VERY_BLURRED = "VERY_BLURRED"
    CUT_OFF = "CUT_OFF"


@dataclass
class TestCase:
    id: int
    letter_id: int
    image_selection: ImageSelection
    household_id: int


@dataclass
class TestResult:
    match_found: bool
    correct_recipient_ids: bool
    correct_image_id: bool
    model_test_id: int
    complete_response: str
    error_msg: str
    time: float
    extracted_text: str
    tesseract_time: float | None = None
    llama_time: float | None = None


@dataclass
class ModelAnswerCheck:
    match_found: bool
    correct_recipient_ids: bool
    correct_image_id: bool
    error_msg: str


class ModelFamily(Enum):
    Qwen3 = "Qwen3"
    Llama = "Llama"


@dataclass
class Model:
    id: int
    name: str
    family: ModelFamily


@dataclass
class Timings:
    time: float
    tesseract_time: float | None = None
    llama_time: float | None = None


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
