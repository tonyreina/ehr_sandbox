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
| `--ehr` | `EHR_TYPE` | Backend for this run: `epic`, `cerner` or `hapi` |

## Examples

```bash
pixi run observations                              # theodore, laboratory
pixi run observations camila --category vital-signs
pixi run observations camila --count 5
pixi run observations derrick --ehr epic --category social-history
pixi run observations nancy --ehr cerner --category vital-signs --count 5
```

Sandbox data is sparse and differs per patient (for example `linda` has no laboratory results on Epic, and `olivia` has no observations at all); when nothing is printable the command says so. Numeric, coded and text values are printed, and blood pressure shows its components. `derrick` and `elijah` only have smoking history: `pixi run observations derrick --ehr epic --category social-history`.

## Example output

```
EHR: Epic
Laboratory results for theodore (e63wRTbPfr1p8UW81d8Seiw3):

  2006-07-07  Hemoglobin A1C: 7.1 %
  2012-10-19  Hemoglobin: 15.0 g/dL
  2009-03-12  Hemoglobin: 15 g/dL
  2012-10-19  Hematocrit: 45 %
  ...
```

### Cerner

```
$ pixi run observations nancy --ehr cerner --category vital-signs --count 5
EHR: Cerner
Vital-signs results for nancy (12724066):

  2099-07-07  Temperature Oral: 31.0 degC
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
