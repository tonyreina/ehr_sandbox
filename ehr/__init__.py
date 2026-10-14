"""EHR client package — import all clients to trigger factory registration."""
from ehr.base import BaseEHRClient
from ehr.factory import ClientFactory

import ehr.epic    # noqa: F401 — registers "epic"
import ehr.cerner  # noqa: F401 — registers "cerner"
import ehr.hapi    # noqa: F401 — registers "hapi"

__all__ = ["BaseEHRClient", "ClientFactory"]
