# Demo 2: Observations

Queries observations for a patient and prints each result with its date, name, value, and unit.

## Usage

```bash
pixi run observations [name] [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| name | `theodore` | Patient key (camila, derrick, theodore, linda) |
| `--category` | `laboratory` | FHIR observation category |
| `--count`, `-n` | `20` | Max results to return |

## Examples

```bash
# Lab results for Theodore (default)
pixi run observations

# Vital signs for Camila
pixi run observations camila --category vital-signs

# Last 5 labs for Linda
pixi run observations linda --count 5
```

## Example output

```
Laboratory results for theodore (e63wRTbPfr1p8UW81d8Seiw3):

  2006-07-07  Hemoglobin A1C: 7.1 %
  2012-10-19  Hemoglobin: 15.0 g/dL
  2012-10-19  Hematocrit: 45 %
  2007-07-25  Glucose, Ur: 110 mg/dL
  2007-07-25  Platelets: 200 K/µL
```

## FHIR query

Calls `GET /Observation` with:

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
