from abc import ABC, abstractmethod

class BaseService(ABC):
    """Marker for domain-level business services."""

    @abstractmethod
    def validate(self) -> None:
        """
        Perform any a priori checks before service methods run.
        Raise appropriate exceptions on invalid state.
        """
        ...
