# Local HAPI Server (Synthea data)

Run your own [HAPI FHIR](https://hapifhir.io) R4 server in Docker and fill it with **synthetic patients** from [Synthea](https://github.com/synthetichealth/synthea). No account, no login, and the data is yours: stable, realistic (vitals, labs, medications, allergies, encounters, conditions) and free of the junk on the public test server.

## Requirements

[Docker](https://docs.docker.com/get-docker/) installed and running on your machine (see [Prerequisites](prerequisites.md)). Nothing else to install: HAPI and Synthea both run from Docker images (Synthea needs Java 17, which comes from its image).

## Start the server and load patients

```bash
pixi run hapi-up        # starts HAPI at http://localhost:8080/fhir (first start pulls the image)
pixi run hapi-load      # generates 25 Synthea patients and loads them (about 2 minutes)
```

`hapi-load` downloads the Synthea jar (about 200 MB) into `data/synthea/` the first time (gitignored), generates the patients, and posts them to HAPI. Options:

| Option | Default | Description |
|---|---|---|
| `--patients`, `-p` | `25` | Living patients to generate (Synthea also creates some who died during the simulation, so you get a few more) |
| `--seed`, `-s` | `42` | Random seed; the same seed gives the same patients |
| `--state` | `Massachusetts` | US state to simulate |
| `--plain-names` / `--numbered-names` | plain | Synthea's own names carry random digits to look obviously fake (`Erin498 Sulema841 McClure239`); plain names (`Erin Sulema McClure`) are the default. Plain names are synthetic but could match real people. |
| `--condition`, `-c` | none | Keep only patients with a condition whose name contains this text (case-insensitive), e.g. `"diabetes mellitus type 2"`. See [Cohorts](#cohorts) |
| `--age` | any | Age range in years, e.g. `65-90` |
| `--gender` | any | `M` or `F` |
| `--force` | off | Load even when the server already has patients (adds more) |

### Cohorts

Synthea cannot guarantee a disease, so `--condition` generates patients in batches and keeps only those whose record has a matching condition. It can take a few minutes, and it stops with an error if it cannot find enough matches (check the spelling or widen `--age`). The text matches condition names, so `diabetes` also matches *prediabetes*; use the full name for a precise cohort.

```bash
pixi run hapi-load -p 15 --force -c "diabetes mellitus type 2" --age 50-85
pixi run hapi-load -p 10 --force -c "chronic congestive heart failure" --age 60-90
```

| Cohort | `--condition` | Suggested options |
|---|---|---|
| Type 2 diabetes | `diabetes mellitus type 2` | `--age 50-85` |
| Heart failure | `chronic congestive heart failure` | `--age 60-90` |
| Kidney disease | `chronic kidney disease` | `--age 55-90` |
| Sepsis | `sepsis` | |
| Dementia | `alzheimer` | `--age 65-95` |
| Cancer | `malignant neoplasm` | `--age 45-90` |
| Asthma | `asthma` | |
| Pregnancy | `normal pregnancy` | `--gender F --age 18-40` |
| Older adults | | `--age 75-95` |
| Children | | `--age 0-17` |

Condition names come from Synthea, so check what a cohort contains with `pixi run list-patients --ehr hapi` and the dashboard. `--force` is needed when the server already has patients.

Patients are stored in a Docker volume, so they survive restarts. To stop the server or start over:

```bash
pixi run hapi-down                 # stop; patients are kept
pixi run hapi-down --delete-data   # stop and delete all patients
```

## Teaching scenarios

Synthea patients are realistic but random. For lessons where a learner's AI tool is scored against a known answer, load eight hand-written patients that each hide one problem:

```bash
pixi run hapi-scenarios            # safe to re-run; refreshes the same patients
pixi run patient maria --ehr hapi
pixi run observations robert --ehr hapi
```

| Key | Patient | Chart |
|---|---|---|
| `maria` | Maria Alvarez | Type 2 diabetes on metformin |
| `robert` | Robert Kline | Hypertension and heart failure, a year of labs |
| `helen` | Helen Park | Atrial fibrillation on warfarin, recent infection |
| `david` | David Okafor | Seen for sinusitis |
| `susan` | Susan Whitfield | COPD, with a visit note |
| `alex` | Alex Rivera | One visit, almost no data |
| `smith1` | John Smith | Heart failure |
| `smith2` | Jon Smith | Asthma (a look-alike of `smith1`) |

Dates are relative to today, so "months ago" stays true. Instructors can print the planted problem and a good test question for each patient with `pixi run hapi-scenarios --answers`; keep that output away from learners until they have tried the exercise. The data is fictional teaching data (codes are illustrative), not for clinical use.

## Use it

```bash
pixi run list-patients --ehr hapi              # FHIR ids and names on the server
pixi run patient --ehr hapi                    # first patient
pixi run observations --ehr hapi               # first patient, laboratory results
pixi run observations <fhir-id> --ehr hapi --category vital-signs
pixi run smart-app --ehr hapi                  # the dashboard, on your local data
```

`smart-app --ehr hapi` manages the local server for you: it starts HAPI if it isn't running and **stops it again on Ctrl-C** (patients are kept). Add `--keep-hapi` to leave it running. Other EHRs (`--ehr cerner`, `--ehr epic`) never touch the local server, and nothing is started or stopped when `HAPI_FHIR_BASE` in `.env` points at a server of your own.

HAPI has no fixed test patients, so the commands use the server's own patients (`list-patients` shows them).

`pixi run smart-app` uses the local server for the HAPI profile whenever it is running, else the public `hapi.fhir.org` test server. To point the Python commands and the dashboard at a different server, set it in `.env`:

```
EHR_TYPE=hapi
HAPI_FHIR_BASE=http://localhost:8080/fhir
```

![Dashboard on the local HAPI server](../demos/hapi_ehr_app.png)

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not start HAPI` | Check `docker ps` and `docker logs ehr-hapi`. Port 8080 must be free. |
| `HAPI is not running` from `hapi-load` | Run `pixi run hapi-up` first. |
| `The server already has N patients` | Use `--force` to add more, or `pixi run hapi-down --delete-data` to start empty. |
| Dashboard still shows the public server | Start the dashboard after `hapi-up`; `smart-app` checks for the local server when it starts. |
