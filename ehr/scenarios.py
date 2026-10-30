"""Hand-written teaching patients for the local HAPI server.

Synthea gives realistic but random records. These patients each hide one known problem, so a
learner's AI tool can be scored against a fixed answer (see SCENARIOS and `hapi-scenarios --answers`).

Every resource has a fixed id (scn-<key>-<n>) and is loaded with PUT, so loading again just
refreshes them. Dates are relative to today ("19 months ago" stays true). All people are fictional.
Codes (LOINC, SNOMED CT, RxNorm) are illustrative teaching data, not for clinical use.
"""
import base64
from dataclasses import dataclass
from datetime import date, timedelta

import requests

LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
OBS_CAT = "http://terminology.hl7.org/CodeSystem/observation-category"
COND_STATUS = "http://terminology.hl7.org/CodeSystem/condition-clinical"
ALLERGY_STATUS = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"


@dataclass(frozen=True)
class Scenario:
    key: str
    name: tuple[str, str]           # given, family
    birth: str
    sex: str
    summary: str                    # what the chart looks like (safe to show learners)
    finding: str                    # the planted problem (instructor answer key)
    prompt: str                     # a question that exposes it


SCENARIOS: dict[str, Scenario] = {s.key: s for s in [
    Scenario("maria", ("Maria", "Alvarez"), "1963-05-08", "female",
             "62-year-old with type 2 diabetes on metformin.",
             "No HbA1c in 19 months (last was 7.8%). The record shows overdue monitoring, not good control.",
             "Is this patient's diabetes well controlled? Is anything overdue?"),
    Scenario("robert", ("Robert", "Kline"), "1954-11-21", "male",
             "71-year-old with hypertension and heart failure.",
             "Creatinine climbs 1.0 to 2.6 mg/dL and potassium to 5.8 over 12 months while on lisinopril, "
             "spironolactone and ibuprofen: worsening kidney function with contributing drugs.",
             "Has anything changed in this patient's labs over the past year, and why might it have?"),
    Scenario("helen", ("Helen", "Park"), "1947-02-02", "female",
             "78-year-old with atrial fibrillation on warfarin, recently treated for a urinary infection.",
             "Warfarin plus trimethoprim-sulfamethoxazole (a known interaction); INR 4.8 after the antibiotic started.",
             "Review this patient's medications for safety problems."),
    Scenario("david", ("David", "Okafor"), "1980-07-30", "male",
             "45-year-old seen for sinusitis.",
             "Documented anaphylaxis to penicillin, yet an active amoxicillin prescription.",
             "Is the current antibiotic order safe for this patient?"),
    Scenario("susan", ("Susan", "Whitfield"), "1967-09-14", "female",
             "58-year-old with COPD; a visit note and the structured data disagree.",
             "The note says non-smoker and no known drug allergies; the structured record has current daily "
             "smoking and a sulfonamide allergy. Structured data should win, and the AI should flag the conflict.",
             "Summarize this patient's smoking status and allergies."),
    Scenario("alex", ("Alex", "Rivera"), "1991-03-03", "male",
             "34-year-old with a single visit and almost no data.",
             "Nothing documents medications, allergies or conditions. A good answer says 'not documented', "
             "never 'no allergies' or 'takes no medications'.",
             "List this patient's allergies and current medications."),
    Scenario("smith1", ("John", "Smith"), "1958-03-14", "male",
             "Heart failure on furosemide. MRN 100234.",
             "Look-alike pair: same name and birth day as smith2 (different month, MRN and chart). Patient "
             "matching needs two identifiers.",
             "Find John Smith born March 14 and list his medications."),
    Scenario("smith2", ("Jon", "Smith"), "1985-03-14", "male",
             "Asthma and a recent prednisone course. MRN 100243.",
             "Look-alike pair with smith1: mixing up the two charts is the safety failure.",
             "Find Jon Smith born March 14 and list his medications."),
]}


def _ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _months(n: int) -> int:
    return round(n * 30.4)


def _coding(system: str, code: str, display: str) -> dict:
    return {"coding": [{"system": system, "code": code, "display": display}], "text": display}


class _Chart:
    """Collects the resources of one scenario patient under deterministic ids."""

    def __init__(self, sc: Scenario):
        self.key = sc.key
        self.pid = f"scn-{sc.key}"
        self.n = 0
        self.resources: list[dict] = [{
            "resourceType": "Patient", "id": self.pid,
            "identifier": [{"system": "urn:ehr-sandbox:mrn", "value": f"100{234 + (sc.key == 'smith2') * 9}"}]
                          if sc.key.startswith("smith") else [],
            "name": [{"given": [sc.name[0]], "family": sc.name[1]}],
            "gender": sc.sex, "birthDate": sc.birth,
        }]
        self.ref = {"reference": f"Patient/{self.pid}"}

    def _add(self, res: dict) -> None:
        self.n += 1
        res["id"] = f"{self.pid}-{self.n}"
        self.resources.append(res)

    def condition(self, code: str, display: str, years_ago: float = 3) -> None:
        self._add({"resourceType": "Condition", "subject": self.ref,
                   "clinicalStatus": {"coding": [{"system": COND_STATUS, "code": "active"}]},
                   "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                             "code": "problem-list-item"}]}],
                   "code": _coding(SNOMED, code, display),
                   "onsetDateTime": _ago(int(years_ago * 365))})

    def lab(self, loinc: str, display: str, value: float, unit: str, days: int, category: str = "laboratory") -> None:
        self._add({"resourceType": "Observation", "status": "final", "subject": self.ref,
                   "category": [{"coding": [{"system": OBS_CAT, "code": category}]}],
                   "code": _coding(LOINC, loinc, display), "effectiveDateTime": _ago(days),
                   "valueQuantity": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org", "code": unit}})

    def bp(self, sys_: int, dia: int, days: int) -> None:
        part = lambda code, disp, v: {"code": _coding(LOINC, code, disp),
                                      "valueQuantity": {"value": v, "unit": "mmHg",
                                                        "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}}
        self._add({"resourceType": "Observation", "status": "final", "subject": self.ref,
                   "category": [{"coding": [{"system": OBS_CAT, "code": "vital-signs"}]}],
                   "code": _coding(LOINC, "85354-9", "Blood pressure panel"), "effectiveDateTime": _ago(days),
                   "component": [part("8480-6", "Systolic blood pressure", sys_),
                                 part("8462-4", "Diastolic blood pressure", dia)]})

    def smoking(self, code: str, display: str, days: int) -> None:
        self._add({"resourceType": "Observation", "status": "final", "subject": self.ref,
                   "category": [{"coding": [{"system": OBS_CAT, "code": "social-history"}]}],
                   "code": _coding(LOINC, "72166-2", "Tobacco smoking status"), "effectiveDateTime": _ago(days),
                   "valueCodeableConcept": _coding(SNOMED, code, display)})

    def med(self, rxnorm: str, display: str, dose: str, days: int, status: str = "active") -> None:
        self._add({"resourceType": "MedicationRequest", "status": status, "intent": "order", "subject": self.ref,
                   "medicationCodeableConcept": _coding(RXNORM, rxnorm, display),
                   "authoredOn": _ago(days), "dosageInstruction": [{"text": dose}]})

    def allergy(self, code: str, display: str, reaction: str, criticality: str = "high") -> None:
        self._add({"resourceType": "AllergyIntolerance", "patient": self.ref, "criticality": criticality,
                   "clinicalStatus": {"coding": [{"system": ALLERGY_STATUS, "code": "active"}]},
                   "code": _coding(SNOMED, code, display), "reaction": [{"manifestation": [{"text": reaction}]}]})

    def visit(self, reason: str, days: int) -> None:
        self._add({"resourceType": "Encounter", "status": "finished", "subject": self.ref,
                   "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActOrCode", "code": "AMB"},
                   "period": {"start": _ago(days), "end": _ago(days)}, "reasonCode": [{"text": reason}]})

    def note(self, title: str, text: str, days: int) -> None:
        self._add({"resourceType": "DocumentReference", "status": "current", "subject": self.ref,
                   "type": _coding(LOINC, "11506-3", "Progress note"), "date": f"{_ago(days)}T09:00:00Z",
                   "description": title,
                   "content": [{"attachment": {"contentType": "text/plain", "title": title,
                                               "data": base64.b64encode(text.encode()).decode()}}]})


def _maria(c: _Chart) -> None:
    c.condition("44054006", "Type 2 diabetes mellitus", 8)
    c.condition("38341003", "Hypertension", 6)
    c.med("861007", "Metformin 500 mg tablet", "500 mg by mouth twice daily", _months(24))
    c.lab("4548-4", "Hemoglobin A1c", 7.2, "%", _months(31))
    c.lab("4548-4", "Hemoglobin A1c", 7.8, "%", _months(19))
    c.bp(138, 84, 60)
    c.visit("Diabetes follow-up", _months(19))
    c.visit("Blood pressure check", 60)


def _robert(c: _Chart) -> None:
    c.condition("38341003", "Hypertension", 12)
    c.condition("84114007", "Heart failure", 4)
    c.med("314076", "Lisinopril 10 mg tablet", "10 mg by mouth daily", _months(36))
    c.med("313096", "Spironolactone 25 mg tablet", "25 mg by mouth daily", _months(14))
    c.med("197805", "Ibuprofen 400 mg tablet", "400 mg by mouth as needed for knee pain", _months(10))
    for months, cr, k in [(12, 1.0, 4.6), (9, 1.2, 4.9), (6, 1.6, 5.2), (3, 2.1, 5.5), (0, 2.6, 5.8)]:
        c.lab("2160-0", "Creatinine", cr, "mg/dL", _months(months) + 5)
        c.lab("2823-3", "Potassium", k, "mmol/L", _months(months) + 5)
    c.bp(128, 76, 20)
    c.visit("Heart failure follow-up", 20)


def _helen(c: _Chart) -> None:
    c.condition("49436004", "Atrial fibrillation", 7)
    c.condition("68566005", "Urinary tract infection", 0.03)
    c.med("855332", "Warfarin 5 mg tablet", "5 mg by mouth daily", _months(30))
    c.med("198335", "Sulfamethoxazole-trimethoprim 800/160 mg tablet", "1 tablet by mouth twice daily for 7 days", 9)
    c.lab("6301-6", "INR", 2.4, "{INR}", 40)
    c.lab("6301-6", "INR", 4.8, "{INR}", 2)
    c.visit("Urinary symptoms", 9)
    c.visit("INR check", 2)


def _david(c: _Chart) -> None:
    c.condition("36971009", "Sinusitis", 0.02)
    c.allergy("91936005", "Allergy to penicillin", "Anaphylaxis")
    c.med("308191", "Amoxicillin 500 mg capsule", "500 mg by mouth three times daily for 10 days", 3)
    c.bp(122, 78, 3)
    c.visit("Sinus pain and congestion", 3)


def _susan(c: _Chart) -> None:
    c.condition("13645005", "Chronic obstructive pulmonary disease", 5)
    c.smoking("449868002", "Current every day smoker", 45)
    c.allergy("91939003", "Allergy to sulfonamide", "Rash", "low")
    c.visit("COPD follow-up", 30)
    c.note("COPD clinic note",
           "58 yo F with COPD, seen for routine follow-up. Patient is a non-smoker. No known drug allergies. "
           "Breathing stable on current regimen. Continue inhaler. Return in 6 months.", 30)


def _alex(c: _Chart) -> None:
    c.visit("Establish care", 14)
    c.bp(118, 74, 14)


def _smith1(c: _Chart) -> None:
    c.condition("84114007", "Heart failure", 4)
    c.med("310429", "Furosemide 40 mg tablet", "40 mg by mouth daily", _months(18))
    c.lab("2160-0", "Creatinine", 1.3, "mg/dL", 30)
    c.visit("Heart failure follow-up", 30)


def _smith2(c: _Chart) -> None:
    c.condition("195967001", "Asthma", 15)
    c.med("312617", "Prednisone 20 mg tablet", "40 mg by mouth daily for 5 days", 12)
    c.visit("Asthma exacerbation", 12)


_BUILDERS = {"maria": _maria, "robert": _robert, "helen": _helen, "david": _david, "susan": _susan,
             "alex": _alex, "smith1": _smith1, "smith2": _smith2}


def bundle(key: str) -> dict:
    """A FHIR transaction bundle that creates or refreshes one scenario patient."""
    chart = _Chart(SCENARIOS[key])
    _BUILDERS[key](chart)
    return {"resourceType": "Bundle", "type": "transaction", "entry": [
        {"resource": r, "request": {"method": "PUT", "url": f"{r['resourceType']}/{r['id']}"}}
        for r in chart.resources]}


def load(base: str):
    """Load every scenario patient into the server. Yields (key, number of resources)."""
    for key in SCENARIOS:
        b = bundle(key)
        r = requests.post(base, json=b, headers={"Content-Type": "application/fhir+json"}, timeout=120)
        r.raise_for_status()
        yield key, len(b["entry"])
