import arrow
from datetime import datetime
from sqlalchemy import ForeignKey, String, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID
from typing import List

from pii.database.models.core.main import db
from pii.database.models.core.service_object import ServiceObject, ServiceObjectDC
from pii.domain.enums import PersonNameType, GenderType, MaritalStatusType
from dataclasses import MISSING



class History(ServiceObject, db.Model):
    # As an abstract, this doesn't need a domain-level dataclass, so we just
    # inherit ServiceObject and not ServiceObjectDC.
    __abstract__ = True

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)


    @staticmethod
    def current(history_values: List["History"], value_type_name=None, value_type_value=None):
        for value in history_values:
            if not (value.start_date <= arrow.utcnow().naive and
                    (value.end_date is None or value.end_date < arrow.utcnow().naive())):
                continue

            if value_type_name is None and value_type_value is None:
                return value
            elif value_type_name and value_type_value:
                attr_value = getattr(value, value_type_name, MISSING)
                if attr_value is MISSING:
                    raise AttributeError(f"Attribute '{value_type_name}' not found on {value}")
                if attr_value == value_type_value:
                    return value
            else:
                raise ValueError("Both value_type_name and value_type_value must be provided together.")

        return None


class PersonName(History):
    __tablename__ = "person_name"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_type: Mapped[PersonNameType] = mapped_column(SQLEnum(PersonNameType), nullable=False)
    person_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)
    person: Mapped["Person"] = relationship("Person", back_populates="names")

class PersonGender(History):
    __tablename__ = "person_gender"

    gender: Mapped[GenderType] = mapped_column(SQLEnum(GenderType), nullable=False)
    person_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)
    person: Mapped["Person"] = relationship("Person", back_populates="genders")


class MaritalStatus(History):
    __tablename__ = "marital_status"

    status: Mapped[MaritalStatusType] = mapped_column(SQLEnum(MaritalStatusType), nullable=False)
    person_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("person.id"), nullable=False)
    person: Mapped["Person"] = relationship("Person", foreign_keys=[person_id])