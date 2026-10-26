"""Oracle Health (Cerner) FHIR client for the open sandbox.

The open sandbox is read-only and needs no authentication, so this client
works out of the box:

  EHR_TYPE=cerner

Optionally override the endpoint (defaults to the public sandbox tenant):

  CERNER_FHIR_BASE=https://fhir-open.cerner.com/r4/<tenant-id>

Secured (authenticated) Cerner endpoints are not implemented.
"""
import os

import requests
from dotenv import load_dotenv

from ehr.base import BaseEHRClient
from ehr.factory import ClientFactory

# Public Oracle Health sandbox tenant
_DEFAULT_BASE = "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d"


@ClientFactory.register("cerner")
class CernerClient(BaseEHRClient):
    """No-auth FHIR client for the Oracle Health open sandbox."""

    def __init__(self, fhir_base_url: str = _DEFAULT_BASE) -> None:
        self._fhir_base = fhir_base_url.rstrip("/")
        self._session   = requests.Session()
        self._session.headers["Accept"] = "application/fhir+json"

    @property
    def ehr_name(self) -> str:
        return "Cerner"

    @property
    def fhir_base(self) -> str:
        return self._fhir_base

    def get_patient(self, patient_id: str) -> dict:
        r = self._session.get(f"{self._fhir_base}/Patient/{patient_id}")
        r.raise_for_status()
        return r.json()

    def get_observations(
        self,
        patient_id: str,
        category: str = "laboratory",
        count: int = 20,
    ) -> list[dict]:
        r = self._session.get(f"{self._fhir_base}/Observation", params={
            "patient":  patient_id,
            "category": category,
            "_sort":    "-date",
            "_count":   str(count),
        })
        r.raise_for_status()
        return [e["resource"] for e in r.json().get("entry", [])]

    @classmethod
    def from_env(cls) -> "CernerClient":
        load_dotenv(override=True)
        return cls(fhir_base_url=os.getenv("CERNER_FHIR_BASE", _DEFAULT_BASE))
