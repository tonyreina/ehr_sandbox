"""ClientFactory — registry-based EHR client selection."""
import os
from dotenv import load_dotenv
from ehr.base import BaseEHRClient


class ClientFactory:
    _registry: dict[str, type[BaseEHRClient]] = {}

    @classmethod
    def register(cls, ehr_type: str):
        """Decorator that registers an EHR client class under *ehr_type*."""
        def decorator(klass: type[BaseEHRClient]) -> type[BaseEHRClient]:
            cls._registry[ehr_type] = klass
            return klass
        return decorator

    @classmethod
    def from_env(cls) -> BaseEHRClient:
        """Return a client for the EHR named in EHR_TYPE (default: epic)."""
        load_dotenv(override=True)
        ehr_type = os.getenv("EHR_TYPE", "epic").lower()
        if ehr_type not in cls._registry:
            available = ", ".join(cls._registry)
            raise ValueError(
                f"Unknown EHR_TYPE={ehr_type!r}. Available: {available}"
            )
        return cls._registry[ehr_type].from_env()

    @classmethod
    def available(cls) -> list[str]:
        """Return names of all registered EHR clients."""
        return list(cls._registry)
