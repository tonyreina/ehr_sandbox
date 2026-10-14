"""Cerner (Oracle Health) FHIR client — stub showing the extension pattern.

Cerner uses the same JWT client-credentials flow as Epic (RS384).
To implement:
  1. Set EHR_TYPE=cerner in .env
  2. Add CERNER_CLIENT_ID, CERNER_TENANT_ID to .env
  3. Register a JWKS URL in the Cerner developer portal
  4. Fill in _fetch_token() below — the flow is nearly identical to EpicClient
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from ehr.base import BaseEHRClient
from ehr.factory import ClientFactory


@ClientFactory.register("cerner")
class CernerClient(BaseEHRClient):

    def __init__(self, client_id: str, tenant_id: str, key_file: Path) -> None:
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._key_file  = key_file

    @property
    def ehr_name(self) -> str:
        return "Cerner"

    @property
    def fhir_base(self) -> str:
        return f"https://fhir-ehr.cerner.com/r4/{self._tenant_id}"

    @property
    def _token_url(self) -> str:
        return (
            f"https://authorization.cerner.com/tenants/{self._tenant_id}"
            "/protocols/oauth2/profiles/smart-v1/token"
        )

    def _session_(self) -> requests.Session:
        # TODO: implement JWT client-credentials fetch (same pattern as EpicClient)
        raise NotImplementedError(
            "CernerClient authentication not yet implemented. "
            "See ehr/cerner.py for the extension points."
        )

    def get_patient(self, patient_id: str) -> dict:
        r = self._session_().get(f"{self.fhir_base}/Patient/{patient_id}")
        r.raise_for_status()
        return r.json()

    def get_observations(
        self,
        patient_id: str,
        category: str = "laboratory",
        count: int = 20,
    ) -> list[dict]:
        r = self._session_().get(f"{self.fhir_base}/Observation", params={
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
        root = Path(__file__).parent.parent
        return cls(
            client_id = os.environ["CERNER_CLIENT_ID"],
            tenant_id = os.environ["CERNER_TENANT_ID"],
            key_file  = root / "keys" / "private_key.pem",
        )
