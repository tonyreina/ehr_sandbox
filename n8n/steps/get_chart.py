"""Read the patient's chart from the practice server: this decides which records the AI gets to see.

The n8n workflow sends the referral request to run(). What run() returns goes to the next step, Build the prompt.
Edit this file in VS Code and save it: the next draft uses your change. No restart, no publishing.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

# The practice server. Inside the workflow containers it is called ehr-hapi.
HAPI_BASE = os.environ.get("HAPI_BASE", "http://ehr-hapi:8080/fhir")

# ---- What to read (change these) ---------------------------------------------------------------
# One line for each kind of record: a name, the kind of record, and how to search for it.
# {patient} becomes the patient's id. "_count" is the most records to get. "_sort": "-date" means newest first.
# Build the prompt looks for problems, medications, allergies and labs. A record you add here is read, but the AI
# only sees it once you also add it to the chart text in build_prompt.py.
READS = {
    "problems": ("Condition", {"patient": "{patient}", "_count": "50"}),
    "medications": ("MedicationRequest", {"patient": "{patient}", "_count": "50"}),
    "allergies": ("AllergyIntolerance", {"patient": "{patient}", "_count": "50"}),
    "labs": ("Observation", {"patient": "{patient}", "category": "laboratory", "_sort": "-date", "_count": "100"}),
}


def fetch(path: str, params: dict | None = None) -> dict:
    """GET one record, or one search, from the practice server."""
    url = f"{HAPI_BASE}/{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/fhir+json"}), timeout=30) as reply:
            return json.load(reply)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"The practice server answered {e.code} for {path}. Is the patient or visit id right?") from None
    except OSError as e:
        raise RuntimeError(f"Could not reach the practice server at {HAPI_BASE} ({e.reason if hasattr(e, 'reason') else e}). Is `pixi run hapi-up` running?") from None


def run(request: dict) -> dict:
    patient = urllib.parse.quote(str(request.get("patientId", "")), safe="")
    visit = urllib.parse.quote(str(request.get("encounterId", "")), safe="")
    chart = {
        "request": request,
        "patient": fetch(f"Patient/{patient}"),
        "encounter": fetch(f"Encounter/{visit}"),
    }
    for name, (kind, params) in READS.items():
        chart[name] = fetch(kind, {key: value.format(patient=patient) for key, value in params.items()})
    return chart
