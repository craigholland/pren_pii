from abc import ABC, abstractmethod
from typing import Any, Type


class BaseValidatorService(ABC):
    @classmethod
    def validate(cls, instance: Any) -> None:
        """
        Runs all validation methods prefixed with 'validate__'.
        Each method must accept the instance being validated.
        """
        for attr_name in dir(cls):
            if attr_name.startswith("validate__"):
                method = getattr(cls, attr_name)
                if callable(method):
                    method(instance)
