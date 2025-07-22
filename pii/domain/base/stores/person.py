from pii.common.abstracts.base_store_nodb import BaseStore_NoDB
from pii.domain.base.dataclasses import (
    Person,
)

class PersonStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for Person entities.
    """
    _dc_model = Person