"""HAPI FHIR client — unauthenticated, for local dev and testing.

Start a local HAPI server filled with Synthea patients with:
  pixi run hapi-up
  pixi run hapi-load

Then set in .env (or pass --ehr hapi):
  EHR_TYPE=hapi
  HAPI_FHIR_BASE=http://localhost:8080/fhir
"""
import os

import requests
from dotenv import load_dotenv

from ehr.base import BaseEHRClient
from ehr.factory import ClientFactory

_DEFAULT_BASE = "http://localhost:8080/fhir"


@ClientFactory.register("hapi")
class HapiFhirClient(BaseEHRClient):
    """No-auth FHIR client for a local HAPI FHIR server."""

    def __init__(self, fhir_base_url: str = _DEFAULT_BASE) -> None:
        self._fhir_base = fhir_base_url.rstrip("/")
        self._session   = requests.Session()
        self._session.headers["Accept"] = "application/fhir+json"

    @property
    def ehr_name(self) -> str:
        return "HAPI FHIR"

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

    def list_patients(self, count: int = 20) -> list[dict]:
        """First *count* Patient resources on the server (HAPI has no fixed test patients)."""
        r = self._session.get(f"{self._fhir_base}/Patient", params={"_count": str(count), "_sort": "family"})
        r.raise_for_status()
        return [e["resource"] for e in r.json().get("entry", []) if e["resource"].get("resourceType") == "Patient"]

    @classmethod
    def from_env(cls) -> "HapiFhirClient":
        load_dotenv(override=True)
        return cls(fhir_base_url=os.getenv("HAPI_FHIR_BASE", _DEFAULT_BASE))
