# pii/common/enums/person_name_type.py

from enum import Enum

class PersonNameType(Enum):
    """
    Overview
    =========
    Contains person name types such as first, last, etc.
    """

    FIRST = 1
    LAST = 2
    MIDDLE = 3
    ALIAS = 4
    NICKNAME = 5
    PREFIX = 6
    SUFFIX = 7
    INITIALS = 8
    PREFERRED = 9

class MaritalStatusType(Enum):
    """
    Overview
    =========
    Enum for marital status types.

    Relationships
    =========
    Used by MaritalStatus model.
    """

    SINGLE = 1
    MARRIED = 2
    DIVORCED = 3
    WIDOWED = 4
    SEPARATED = 5
    PARTNERED = 6
    UNKNOWN = 7


from enum import Enum


class GenderType(Enum):
    """
    Overview
    =========
    Enum for gender types.

    Relationships
    =========
    Used by PersonGender model.
    """

    MALE = 1
    TRANS_MALE = 2
    FEMALE = 3
    TRANS_FEMALE = 4
    NON_BINARY = 5
    OTHER = 6
    UNDISCLOSED = 7
