# Demo 1: Patient Demographics

Fetches a patient record via the active EHR client and prints name, DOB, and gender.

## Usage

```bash
pixi run patient [camila|derrick|theodore|linda]
```

Defaults to `camila`. The EHR backend is determined by `EHR_TYPE` in `.env`.

## Example output

```
EHR:     Epic
Patient: Camila Lopez
DOB:     1987-09-12
Gender:  female
ID:      erXuFYUfucBZaryVksYEcMg3
```

## Known sandbox patients (Epic)

Run `pixi run list-patients` for the full table.

| Key | Name | DOB | Sex | FHIR ID |
|---|---|---|---|---|
| `camila` | Camila Lopez | 1987-09-12 | F | `erXuFYUfucBZaryVksYEcMg3` |
| `derrick` | Derrick Lin | 1973-06-03 | M | `eq081-VQEgP8drUUqCWzHfw3` |
| `theodore` | Theodore Mychart | 1948-07-07 | M | `e63wRTbPfr1p8UW81d8Seiw3` |
| `linda` | Linda Ross | 1969-04-27 | F | `eIXesllypH3M9tAA5WdJftQ3` |

## How it works

`demos/demo_01_patient.py` calls `ClientFactory.from_env()` which returns whichever `BaseEHRClient` matches `EHR_TYPE`. The same script runs unchanged against Epic, HAPI, or any other registered backend.

```python
from ehr import ClientFactory

client  = ClientFactory.from_env()
patient = client.get_patient(patient_id)
```

## FHIR resource

Reads from the R4 `Patient` resource:

- `name[0].given[0]` — first name
- `name[0].family` — last name
- `birthDate` — date of birth
- `gender` — administrative gender
