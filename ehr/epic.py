"""Epic (backend system / client credentials) FHIR client."""
import json
import os
import time
import uuid
from pathlib import Path

import jwt
import requests
from dotenv import load_dotenv

from ehr.base import BaseEHRClient
from ehr.factory import ClientFactory

_TOKEN_BUFFER = 60  # refresh this many seconds before expiry


@ClientFactory.register("epic")
class EpicClient(BaseEHRClient):
    """Authenticates via JWT client-credentials (RS384) — no user login required."""

    def __init__(
        self,
        client_id: str,
        fhir_base_url: str,
        token_url: str,
        key_file: Path,
        jwks_file: Path,
    ) -> None:
        self._client_id   = client_id
        self._fhir_base   = fhir_base_url
        self._token_url   = token_url
        self._key_file    = key_file
        self._jwks_file   = jwks_file
        self._session:    requests.Session | None = None
        self._token_exp:  float = 0.0

    # ------------------------------------------------------------------ props

    @property
    def ehr_name(self) -> str:
        return "Epic"

    @property
    def fhir_base(self) -> str:
        return self._fhir_base

    # ------------------------------------------------------------------ auth

    def _kid(self) -> str:
        with open(self._jwks_file) as f:
            return json.load(f)["keys"][0]["kid"]

    def _fetch_token(self) -> tuple[str, float]:
        with open(self._key_file, "rb") as f:
            private_key = f.read()

        now = int(time.time())
        claims = {
            "iss": self._client_id,
            "sub": self._client_id,
            "aud": self._token_url,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 300,
        }
        signed_jwt = jwt.encode(
            claims, private_key, algorithm="RS384", headers={"kid": self._kid()}
        )
        resp = requests.post(self._token_url, data={
            "grant_type":            "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion":      signed_jwt,
        })
        resp.raise_for_status()
        data = resp.json()
        expires_in = data.get("expires_in", 3600)
        return data["access_token"], time.time() + expires_in

    def _session_(self) -> requests.Session:
        if self._session is None or time.time() >= self._token_exp - _TOKEN_BUFFER:
            token, self._token_exp = self._fetch_token()
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept":        "application/fhir+json",
            })
        return self._session

    # ------------------------------------------------------------------ FHIR

    def get_patient(self, patient_id: str) -> dict:
        r = self._session_().get(f"{self._fhir_base}/Patient/{patient_id}")
        r.raise_for_status()
        return r.json()

    def get_observations(
        self,
        patient_id: str,
        category: str = "laboratory",
        count: int = 20,
    ) -> list[dict]:
        r = self._session_().get(f"{self._fhir_base}/Observation", params={
            "patient":  patient_id,
            "category": category,
            "_sort":    "-date",
            "_count":   str(count),
        })
        r.raise_for_status()
        return [e["resource"] for e in r.json().get("entry", [])]

    # ------------------------------------------------------------------ factory

    @classmethod
    def from_env(cls) -> "EpicClient":
        load_dotenv(override=True)
        root = Path(__file__).parent.parent
        return cls(
            client_id    = os.environ["EPIC_CLIENT_ID"],
            fhir_base_url= os.environ["EPIC_FHIR_BASE"],
            token_url    = os.environ["EPIC_TOKEN_URL"],
            key_file     = root / "keys" / "private_key.pem",
            jwks_file    = root / "keys" / "public_jwks.json",
        )
