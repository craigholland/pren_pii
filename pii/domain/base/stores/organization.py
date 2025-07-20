from pii.common.abstracts.base_store_nodb import BaseStore_NoDB
from pii.domain.base.dataclasses import (
    Organization,
)

class OrganizationStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for Food entities.
    """
    _dc_model = Organization