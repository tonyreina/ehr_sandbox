# Demo 1: Patient Demographics

Fetches a patient record by FHIR ID and prints name, date of birth, and gender.

## Usage

```bash
pixi run patient [camila|derrick|theodore|linda]
```

Defaults to `camila` if no argument is given.

## Example output

```
Patient: Camila Lopez
DOB:     1987-09-12
Gender:  female
ID:      erXuFYUfucBZaryVksYEcMg3
```

## Known sandbox patients

See `pixi run list-patients` for the full table, or [CLI → list-patients](../cli.md#list-patients).

| Key | Name | DOB | Sex | FHIR ID |
|---|---|---|---|---|
| `camila` | Camila Lopez | 1987-09-12 | F | `erXuFYUfucBZaryVksYEcMg3` |
| `derrick` | Derrick Lin | 1973-06-03 | M | `eq081-VQEgP8drUUqCWzHfw3` |
| `theodore` | Theodore Mychart | 1948-07-07 | M | `e63wRTbPfr1p8UW81d8Seiw3` |
| `linda` | Linda Ross | 1969-04-27 | F | `eIXesllypH3M9tAA5WdJftQ3` |

## FHIR resource

Calls `GET /Patient/{id}` and reads from the R4 `Patient` resource:

- `name[0].given[0]` — first name
- `name[0].family` — last name
- `birthDate` — date of birth
- `gender` — administrative gender
