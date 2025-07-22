# prenuvo_pii/domain/food/interface.py
# THIS IS LEGACY CODE.  It is only remaining to serve as example.
# DO NOT USE THIS CODE.  IGNORE IT DURING ANY ANALYSIS
from pii.domain.food.profiles import FoodProfile

class FoodInterface:
    """
    Interface for operating on FoodProfile instances, including importing new records.
    """

    def __init__(self, profile: FoodProfile) -> None:
        if not isinstance(profile, FoodProfile):
            raise TypeError("Expected a FoodProfile instance")
        self.profile = profile

    @classmethod
    def import_many(cls, records: list[dict]) -> list["FoodInterface"]:
        return [cls.import_(record) for record in records]

    @classmethod
    def import_(cls, record: dict) -> "FoodInterface":
        """
        Create & persist a single USDA-JSON record, then return an interface
        wrapping the freshly‐created FoodProfile.
        """
        profile = FoodProfile.create(record)
        return cls(profile)
