"""Build what the AI is told: the instructions, and the chart text it reads.

The n8n workflow sends the records it read from the practice server to run(). What run() returns goes to the AI.
Edit this file in VS Code and save it: the next draft uses your change. No restart, no publishing.

The top of the file is for you to change. The code below it turns the records into text.
"""
from datetime import date

# ---- The words the AI is told (change these) ---------------------------------------------------

ROLE = "You are an assistant helping a clinician draft a referral letter to a specialist. The chart is synthetic teaching data."

RULES = [
    "Use only the chart text provided. Never invent findings, doses, dates or history.",
    'If the letter needs something that is not in the chart, write "Not documented" in its place.',
    "Use plain, professional language. Keep the letter to one page.",
    "The reason for referral is the clinician's reason if one is given; otherwise say what the encounter shows and that no reason was given.",
    "Mention anything in the chart that looks inconsistent or unsafe, so the specialist knows.",
]

# ---- How the letter is laid out (change these) -------------------------------------------------

HEADINGS = [
    "Patient",
    "Reason for referral",
    "Relevant history",
    "Current medications",
    "Allergies",
    "Pertinent results",
    "Question for the specialist",
    "Urgency",
]
CLOSING = "Draft for clinician review. Not sent."
SIGNATURE = "[Referring clinician]"

# ---- The AI model to use if the workflow does not name one -------------------------------------

DEFAULT_MODEL = "gpt-5.3-codex"


def instructions() -> str:
    lines = [ROLE, "", "Rules:"]
    lines += [f"- {rule}" for rule in RULES]
    lines.append(f"- Use these headings: {', '.join(HEADINGS)}.")
    lines.append(f'- End with the line "{CLOSING}" and a signature line "{SIGNATURE}".')
    return "\n".join(lines)


# ---- Turning the records into the chart text the AI reads --------------------------------------

VISIT_CLASS = {"AMB": "Ambulatory visit", "IMP": "Inpatient stay", "EMER": "Emergency visit", "VR": "Virtual visit", "HH": "Home visit"}


def _text(concept: dict | None) -> str:
    concept = concept or {}
    coding = (concept.get("coding") or [{}])[0]
    return concept.get("text") or coding.get("display") or ""


def _records(bundle: dict | None) -> list[dict]:
    return [entry["resource"] for entry in (bundle or {}).get("entry", [])]


def _list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "None documented."


def _age(birth: str | None) -> str:
    try:
        return str(int((date.today() - date.fromisoformat(birth)).days // 365.25))
    except (TypeError, ValueError):
        return "not documented"


def chart_text(data: dict) -> str:
    patient, visit = data.get("patient") or {}, data.get("encounter") or {}
    name = (patient.get("name") or [{}])[0]
    full_name = " ".join([" ".join(name.get("given", [])), name.get("family", "")]).strip() or "Unknown"

    problems = list(dict.fromkeys(filter(None, (_text(r.get("code")) for r in _records(data.get("problems"))))))
    medications = []
    for r in _records(data.get("medications")):
        if r.get("status") == "active":
            dose = ((r.get("dosageInstruction") or [{}])[0]).get("text")
            medications.append(_text(r.get("medicationCodeableConcept")) + (f" - {dose}" if dose else ""))
    allergies = []
    for r in _records(data.get("allergies")):
        reaction = ", ".join(filter(None, (m.get("text") for m in ((r.get("reaction") or [{}])[0]).get("manifestation", []))))
        allergies.append(_text(r.get("code")) + (f" ({reaction})" if reaction else ""))

    latest = {}                                       # the most recent value of each lab test
    for r in _records(data.get("labs")):
        quantity, when = r.get("valueQuantity"), r.get("effectiveDateTime") or ""
        test = _text(r.get("code"))
        if quantity and (test not in latest or when > latest[test][0]):
            latest[test] = (when, quantity.get("value"), quantity.get("unit"))
    results = [f"{test}: {value} {unit} ({when[:10]})" for test, (when, value, unit) in latest.items()]

    kind = ((visit.get("type") or [{}])[0]).get("text") or VISIT_CLASS.get((visit.get("class") or {}).get("code"), "") \
        or (visit.get("class") or {}).get("code") or "Encounter"
    return "\n".join([
        f"Patient: {full_name}",
        f"{patient.get('gender') or 'sex not documented'}, {_age(patient.get('birthDate'))} years, born {patient.get('birthDate') or 'not documented'}",
        "",
        "== Encounter being referred from ==",
        f"Date: {(visit.get('period') or {}).get('start', '')[:10] or 'not documented'}",
        f"Type: {kind}",
        f"Reason: {((visit.get('reasonCode') or [{}])[0]).get('text') or 'not documented'}",
        f"Status: {visit.get('status') or 'not documented'}",
        "",
        "== Problem list ==", _list(problems),
        "",
        "== Current medications ==", _list(medications),
        "",
        "== Allergies ==", _list(allergies),
        "",
        "== Results (latest of each test) ==", _list(results),
    ])


def run(data: dict) -> dict:
    if data.get("error"):                              # reading the chart failed: pass the message on
        return {"error": data["error"]}
    ask = data.get("request") or {}
    reason = ask.get("reason") or "Not provided. Say what the encounter shows and that no reason was given."
    user = (f"CHART:\n{chart_text(data)}\n\nREFERRAL REQUEST\nSpecialty: {ask.get('specialty') or 'not given'}\n"
            f"Urgency: {ask.get('urgency') or 'Routine'}\nClinician's reason for referral: {reason}")
    system = instructions()
    return {
        "request": {"model": data.get("model") or DEFAULT_MODEL, "instructions": system, "input": user, "store": False},
        "sees": {"system": system, "user": user},     # shown in "What the AI sees"
    }
