"""Abstract base class that every EHR client must implement."""
from abc import ABC, abstractmethod


class BaseEHRClient(ABC):

    @property
    @abstractmethod
    def ehr_name(self) -> str:
        """Human-readable name of the EHR system."""

    @property
    @abstractmethod
    def fhir_base(self) -> str:
        """FHIR R4 base URL for this EHR instance."""

    @abstractmethod
    def get_patient(self, patient_id: str) -> dict:
        """Return the raw FHIR Patient resource for *patient_id*."""

    @abstractmethod
    def get_observations(
        self,
        patient_id: str,
        category: str = "laboratory",
        count: int = 20,
    ) -> list[dict]:
        """Return a list of raw FHIR Observation resources for *patient_id*."""

    @classmethod
    @abstractmethod
    def from_env(cls) -> "BaseEHRClient":
        """Construct a client from environment variables."""
