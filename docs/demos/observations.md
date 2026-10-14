# Demo 2: Lab Observations

Queries laboratory observations for a patient and prints each result with its date, name, value, and unit.

## Usage

```bash
pixi run python demo_02_observations.py [name]
```

`name` is one of: `camila`, `derrick`, `theodore`, `linda` (defaults to `theodore`).

## Example output

```
Lab results for patient e63wRTbPfr1p8UW81d8Seiw3:

  2024-03-15  Hemoglobin A1C: 7.1 %
  2024-03-15  Hemoglobin: 15.0 g/dL
  2024-03-15  Hematocrit: 45 %
  2024-02-10  Glucose, Ur: 110 mg/dL
  2024-02-10  Platelets: 200 K/µL
```

## FHIR query

The demo calls `GET /Observation` with these parameters:

| Parameter | Value |
|---|---|
| `patient` | Patient FHIR ID |
| `category` | `laboratory` |
| `_sort` | `-date` (newest first) |
| `_count` | `20` |

Results are filtered to observations with a `valueQuantity` (numeric results).

## Extending the query

To fetch vital signs instead of labs, change `category` to `vital-signs`.  
To filter by LOINC code, add a `code` parameter, e.g. `code=4548-4` for HbA1c.
