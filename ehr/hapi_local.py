"""Run a local HAPI FHIR server (Docker) and fill it with Synthea patients.

Everything shells out to Docker, so the only requirement is a working `docker`:
HAPI runs from its official image with an H2 database in a named volume, and Synthea
runs from a Java 17 image (this machine's Java may be older).
"""
import glob
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import requests

CONTAINER = "ehr-hapi"
VOLUME = "ehr-hapi-data"
HAPI_IMAGE = "hapiproject/hapi:latest"
JAVA_IMAGE = "eclipse-temurin:17-jre"
PORT = 8080
BASE = f"http://localhost:{PORT}/fhir"
NONROOT = "65532"                       # user the HAPI image runs as

SYNTHEA_DIR = Path(__file__).parent.parent / "data" / "synthea"
SYNTHEA_JAR = SYNTHEA_DIR / "synthea-with-dependencies.jar"
SYNTHEA_URL = "https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar"


def _docker(*args: str, check: bool = True, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, text=True, capture_output=True, **kw)


def _exists() -> bool:
    return CONTAINER in _docker("ps", "-a", "--format", "{{.Names}}").stdout.split()


def _running() -> bool:
    return CONTAINER in _docker("ps", "--format", "{{.Names}}").stdout.split()


def ready(base: str = BASE) -> bool:
    try:
        return requests.get(f"{base}/metadata", timeout=3).ok
    except requests.RequestException:
        return False


def up(timeout: int = 240) -> str:
    """Start (creating if needed) the HAPI container and wait until it answers. Returns the base URL."""
    if not _running():
        if _exists():
            _docker("start", CONTAINER)
        else:
            # The image runs as a non-root user, so a fresh volume must be handed over to it first.
            _docker("run", "--rm", "-v", f"{VOLUME}:/data", "busybox", "chown", "-R", f"{NONROOT}:{NONROOT}", "/data")
            _docker(
                "run", "-d", "--name", CONTAINER, "-p", f"{PORT}:8080", "-v", f"{VOLUME}:/data/hapi",
                "-e", "SPRING_DATASOURCE_URL=jdbc:h2:file:/data/hapi/h2;DB_CLOSE_ON_EXIT=FALSE;AUTO_RECONNECT=TRUE",
                "-e", "SPRING_DATASOURCE_USERNAME=sa", "-e", "SPRING_DATASOURCE_PASSWORD=sa",
                "-e", "SPRING_DATASOURCE_DRIVERCLASSNAME=org.h2.Driver",
                "-e", "SPRING_JPA_PROPERTIES_HIBERNATE_DIALECT=ca.uhn.fhir.jpa.model.dialect.HapiFhirH2Dialect",
                "-e", "HAPI_FHIR_ALLOW_EXTERNAL_REFERENCES=true",
                HAPI_IMAGE,
            )
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ready():
            return BASE
        if not _running():
            raise RuntimeError(f"HAPI container stopped; see `docker logs {CONTAINER}`")
        time.sleep(3)
    raise RuntimeError(f"HAPI did not answer within {timeout}s; see `docker logs {CONTAINER}`")


def down(delete_data: bool = False) -> None:
    """Stop and remove the container; the data volume stays unless *delete_data*."""
    if _exists():
        _docker("rm", "-f", CONTAINER)
    if delete_data:
        _docker("volume", "rm", "-f", VOLUME)


def patient_count(base: str = BASE) -> int:
    return requests.get(f"{base}/Patient", params={"_summary": "count"}, timeout=30).json().get("total", 0)


def _run_synthea(patients: int, seed: int, state: str, numbered_names: bool, age: str | None,
                 gender: str | None) -> Path:
    """One Synthea run in Docker (clearing the previous output); returns the bundle directory."""
    SYNTHEA_DIR.mkdir(parents=True, exist_ok=True)
    if not SYNTHEA_JAR.exists():
        urllib.request.urlretrieve(SYNTHEA_URL, SYNTHEA_JAR)
    out = SYNTHEA_DIR / "output"
    for old in glob.glob(str(out / "fhir" / "*.json")):
        os.remove(old)
    cohort = (["-a", age] if age else []) + (["-g", gender] if gender else [])
    _docker(
        "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}", "-v", f"{SYNTHEA_DIR}:/synthea", "-w", "/synthea",
        JAVA_IMAGE, "java", "-jar", SYNTHEA_JAR.name,
        "-p", str(patients), "-s", str(seed), *cohort, "--exporter.baseDirectory=/synthea/output",
        "--exporter.fhir.export=true", "--exporter.fhir.use_us_core_ig=false",
        "--exporter.hospital.fhir.export=true", "--exporter.practitioner.fhir.export=true",
        f"--generate.append_numbers_to_person_names={str(numbered_names).lower()}",
        state,
    )
    return out / "fhir"


def _has_condition(bundle_file: Path, text: str) -> bool:
    """True when the patient bundle has a Condition whose name contains *text* (case-insensitive)."""
    text = text.lower()
    for e in json.loads(bundle_file.read_text()).get("entry", []):
        r = e["resource"]
        if r.get("resourceType") == "Condition" and text in r.get("code", {}).get("text", "").lower():
            return True
    return False


def generate(patients: int, seed: int, state: str, numbered_names: bool = False,
             age: str | None = None, gender: str | None = None, condition: str | None = None) -> Path:
    """Run Synthea in Docker; returns the directory of FHIR bundles.

    Synthea appends random digits to person names (Erin498) so they are obviously fake; by default
    they are left off here.

    *age* is a "min-max" range in years and *gender* is "M" or "F". With *condition* (for example
    "diabetes") only patients who have a matching condition are kept: Synthea cannot guarantee a
    disease, so it is run in batches until enough patients match (raises if it cannot find them).
    """
    if not condition:
        return _run_synthea(patients, seed, state, numbered_names, age, gender)
    cohort = SYNTHEA_DIR / "output" / "fhir-cohort"
    shutil.rmtree(cohort, ignore_errors=True)
    cohort.mkdir(parents=True)
    kept = 0
    batch = min(max(patients * 8, 50), 400)
    for i in range(6):
        fhir = _run_synthea(batch, seed + i, state, numbered_names, age, gender)
        for f in sorted(fhir.glob("*.json")):
            if f.name.startswith(("hospitalInformation", "practitionerInformation")):
                shutil.copy(f, cohort / f.name)
            elif kept < patients and _has_condition(f, condition):
                shutil.copy(f, cohort / f.name)
                kept += 1
        if kept >= patients:
            return cohort
    raise RuntimeError(f"Found only {kept} of {patients} patients with a condition matching {condition!r}; "
                       "check the spelling, widen --age, or ask for fewer patients.")


def load(fhir_dir: Path, base: str = BASE):
    """POST the bundles to the server, hospitals and practitioners first (patients reference them).

    Yields (file name, number of entries) as each bundle is loaded.
    """
    files = sorted(fhir_dir.glob("*.json"))
    infra = [f for f in files if f.name.startswith(("hospitalInformation", "practitionerInformation"))]
    for f in infra + [f for f in files if f not in infra]:
        bundle = json.loads(f.read_text())
        r = requests.post(base, json=bundle, headers={"Content-Type": "application/fhir+json"}, timeout=600)
        r.raise_for_status()
        yield f.name, len(bundle.get("entry", []))
