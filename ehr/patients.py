"""Sandbox test patients, keyed by EHR type.

Each entry is  key -> (FHIR id, display name, birth date, sex).
"""

PATIENTS: dict[str, dict[str, tuple[str, str, str, str]]] = {
    "epic": {
        "camila":   ("erXuFYUfucBZaryVksYEcMg3", "Camila Lopez",     "1987-09-12", "F"),
        "derrick":  ("eq081-VQEgP8drUUqCWzHfw3",  "Derrick Lin",      "1973-06-03", "M"),
        "theodore": ("e63wRTbPfr1p8UW81d8Seiw3",  "Theodore Mychart", "1948-07-07", "M"),
        "linda":    ("eIXesllypH3M9tAA5WdJftQ3",  "Linda Ross",       "1969-04-27", "F"),
        "warren":   ("e0w0LEDCYtfckT6N.CkJKCw3",  "Warren McGinnis",  "1952-05-24", "M"),
        "desiree":  ("eAB3mDIBBcyUKviyzrxsnAw3",  "Desiree Powell",   "2014-11-14", "F"),
        "elijah":   ("egqBHVfQlt4Bw3XGXoxVxHg3",  "Elijah Davis",     "1993-08-18", "M"),
        "olivia":   ("eh2xYHuzl9nkSFVvV3osUHg3",  "Olivia Roberts",   "2003-01-07", "F"),
    },
    "cerner": {
        "nancy": ("12724066", "Nancy Patchtest", "1990-01-02", "F"),
        "joe":   ("12724067", "Joe Testpatient", "1990-05",    "M"),
        "wilm":  ("12724065", "Wilm Smart",      "1990-09-15", "M"),
        "tim":   ("12742400", "Tim Peters",      "1990-09-15", "M"),
    },
    # Teaching scenarios loaded by `pixi run hapi-scenarios` (see ehr/scenarios.py)
    "hapi": {
        "maria":  ("scn-maria",  "Maria Alvarez",   "1963-05-08", "F"),
        "robert": ("scn-robert", "Robert Kline",    "1954-11-21", "M"),
        "helen":  ("scn-helen",  "Helen Park",      "1947-02-02", "F"),
        "david":  ("scn-david",  "David Okafor",    "1980-07-30", "M"),
        "susan":  ("scn-susan",  "Susan Whitfield", "1967-09-14", "F"),
        "alex":   ("scn-alex",   "Alex Rivera",     "1991-03-03", "M"),
        "smith1": ("scn-smith1", "John Smith",      "1958-03-14", "M"),
        "smith2": ("scn-smith2", "Jon Smith",       "1985-03-14", "M"),
    },
}

# (default for `patient`, default for `observations`)
DEFAULTS: dict[str, tuple[str, str]] = {
    "epic":   ("camila", "theodore"),
    "cerner": ("nancy",  "joe"),
}


def patients_for(ehr_type: str) -> dict[str, tuple[str, str, str, str]]:
    """Known test patients for *ehr_type* (empty for backends with none, e.g. hapi)."""
    return PATIENTS.get(ehr_type, {})


def resolve(ehr_type: str, key: str | None, *, observations: bool = False) -> tuple[str, str]:
    """Return (label, FHIR id) for a patient key, defaulting per EHR.

    A *key* that isn't a known test patient is treated as a raw FHIR id.
    """
    table = patients_for(ehr_type)
    if key is None:
        defaults = DEFAULTS.get(ehr_type)
        if defaults is None:
            raise ValueError(f"No default patient for EHR_TYPE={ehr_type!r}; pass a FHIR id.")
        key = defaults[1 if observations else 0]
    if key not in table:
        owners = [e for e, t in PATIENTS.items() if e != ehr_type and key in t]
        if owners:
            raise ValueError(
                f"{key!r} is a test patient for {' / '.join(owners)}, not {ehr_type!r}. "
                f"Use --ehr {owners[0]} (or set EHR_TYPE in .env), or pass a raw FHIR id."
            )
    return key, table[key][0] if key in table else key
