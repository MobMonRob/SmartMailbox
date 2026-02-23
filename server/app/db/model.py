from dataclasses import dataclass
from typing import Optional


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

    def __str__(self) -> str:
        return f"ID: {self.recipient_id}\nHousehold: {self.household_id}\nEmail: {self.email}\nFirstname: {self.firstname}\nMiddlename: {self.middlename}\nSurname: {self.surname}\nTitle: {self.title}\nCountry: {self.country}\nZipcode: {self.zipcode}\nCity: {self.city}\nStreet: {self.street}\nHouse number: {self.house_number}"


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
