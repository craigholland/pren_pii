from pii.database.models.core.validators.base import BaseValidatorService
from pii.domain.enums import PersonNameType
from datetime import datetime


class PersonValidator(BaseValidatorService):
    @classmethod
    def validate__required_names(cls, person):
        name_types = {n.name_type for n in person._names_history}
        required = {PersonNameType.FIRST, PersonNameType.LAST}
        missing = required - name_types
        if missing:
            raise ValueError(f"Missing required name types: {', '.join(t.name for t in missing)}")

    @classmethod
    def validate__dob_not_in_future(cls, person):
        if person.date_of_birth and person.date_of_birth > datetime.utcnow():
            raise ValueError("Date of birth cannot be in the future.")
