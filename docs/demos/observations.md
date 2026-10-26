# Demo 2: Observations

Queries observations for a patient via the active EHR client.

## Usage

```bash
pixi run observations [name] [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| name | `theodore` (Epic) / `joe` (Cerner) | Patient key for the active EHR, or a raw FHIR id |
| `--category` | `laboratory` | FHIR observation category |
| `--count`, `-n` | `20` | Max results to return |

## Examples

```bash
pixi run observations                              # theodore, laboratory
pixi run observations camila --category vital-signs
pixi run observations linda --count 5
```

## Example output

```
EHR: Epic
Laboratory results for theodore (e63wRTbPfr1p8UW81d8Seiw3):

  2006-07-07  Hemoglobin A1C: 7.1 %
  2012-10-19  Hemoglobin: 15.0 g/dL
  2012-10-19  Hematocrit: 45 %
  2007-07-25  Glucose, Ur: 110 mg/dL
```

### Cerner

```
$ EHR_TYPE=cerner pixi run observations nancy --category vital-signs --count 5
EHR: Cerner
Vital-signs results for nancy (12724066):

  2026-10-23  Oxygen Saturation: 97.0 %
  2026-10-23  Temperature Oral: 37.0 degC
```

## How it works

`demos/demo_02_observations.py` uses `ClientFactory.from_env()` — the same call regardless of EHR:

```python
from ehr import ClientFactory

client = ClientFactory.from_env()
obs    = client.get_observations(patient_id, category=category, count=count)
```

## FHIR query

`GET /Observation` with:

| Parameter | Value |
|---|---|
| `patient` | Patient FHIR ID |
| `category` | `laboratory` (or overridden via `--category`) |
| `_sort` | `-date` (newest first) |
| `_count` | `20` (or overridden via `--count`) |

## Observation categories

| Value | Description |
|---|---|
| `laboratory` | Lab results (CBC, metabolic panel, HbA1c, etc.) |
| `vital-signs` | Blood pressure, heart rate, weight, etc. |
| `imaging` | Radiology results |
| `procedure` | Procedure notes |
