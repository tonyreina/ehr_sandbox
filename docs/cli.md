# CLI Reference

All commands are available as pixi tasks (recommended) or via `python cli.py` directly.

The active EHR backend is selected by `EHR_TYPE` in `.env`. Use `list-ehrs` to confirm which one is active. `patient`, `observations`, `list-patients` and `list-ehrs` also take `--ehr epic|cerner|hapi` to use a different backend for one run without editing `.env` (the shell's `EHR_TYPE` does not override `.env`).

---

## patient

Fetch and display demographics for a sandbox test patient.

```bash
pixi run patient [name] [--ehr epic|cerner|hapi]
```

`name` is a test-patient key for the active EHR (see `list-patients`) or a raw FHIR id. Default: `camila` (Epic), `nancy` (Cerner).

**Example:**

```
$ pixi run patient derrick --ehr epic
EHR:     Epic
Patient: Derrick Lin
DOB:     1973-06-03
Gender:  male
ID:      eq081-VQEgP8drUUqCWzHfw3
```

---

## observations

Fetch observations for a patient. Defaults to laboratory results.

```bash
pixi run observations [name] [OPTIONS]   # default: theodore (Epic), joe (Cerner)
```

| Option | Default | Description |
|---|---|---|
| `--category` | `laboratory` | Observation category (`vital-signs`, `imaging`, etc.) |
| `--count`, `-n` | `20` | Maximum number of results |
| `--ehr` | `EHR_TYPE` | Backend for this run: `epic`, `cerner` or `hapi` |

**Examples:**

```bash
pixi run observations theodore --ehr epic
pixi run observations camila --ehr epic --category vital-signs
pixi run observations camila --ehr epic --count 5
pixi run observations derrick --ehr epic --category social-history
pixi run observations nancy --ehr cerner --category vital-signs --count 5
```

Sandbox data is sparse and differs per patient (for example `linda` has no laboratory results on Epic, and `olivia` has no observations at all); when nothing is printable the command says so. Numeric, coded and text values are printed, and blood pressure shows its components. `derrick` and `elijah` only have smoking history: `pixi run observations derrick --ehr epic --category social-history`.

---

## list-patients

Print a table of known test patients for the active `EHR_TYPE`.

```bash
pixi run list-patients [--ehr epic|cerner|hapi]
```

```
Key          Name                 DOB          Sex  FHIR ID
-----------------------------------------------------------
camila       Camila Lopez         1987-09-12   F    erXuFYUfucBZaryVksYEcMg3
derrick      Derrick Lin          1973-06-03   M    eq081-VQEgP8drUUqCWzHfw3
theodore     Theodore Mychart     1948-07-07   M    e63wRTbPfr1p8UW81d8Seiw3
linda        Linda Ross           1969-04-27   F    eIXesllypH3M9tAA5WdJftQ3
warren       Warren McGinnis      1952-05-24   M    e0w0LEDCYtfckT6N.CkJKCw3
desiree      Desiree Powell       2014-11-14   F    eAB3mDIBBcyUKviyzrxsnAw3
elijah       Elijah Davis         1993-08-18   M    egqBHVfQlt4Bw3XGXoxVxHg3
olivia       Olivia Roberts       2003-01-07   F    eh2xYHuzl9nkSFVvV3osUHg3
```

---

## list-ehrs

Show all registered EHR backends and which one is active.

```bash
pixi run list-ehrs
```

```
  epic ← active
  cerner
  hapi
```

Change the active backend by setting `EHR_TYPE` in `.env`. See [EHR Clients](ehr-clients.md) for details.

---

## hapi-up, hapi-down, hapi-load

Run a local HAPI FHIR server in Docker and fill it with synthetic [Synthea](https://github.com/synthetichealth/synthea) patients. See [Local HAPI Server](setup/local-hapi.md).

```bash
pixi run hapi-up                       # start HAPI at http://localhost:8080/fhir
pixi run hapi-load [-p 25] [-s 42]     # generate and load Synthea patients (--numbered-names keeps Synthea's digits)
pixi run hapi-load -c "diabetes mellitus type 2" --age 50-85 --gender F --force   # a cohort (see Local HAPI Server)
pixi run hapi-down [--delete-data]     # stop (patients are kept unless --delete-data)
pixi run hapi-scenarios [--answers]    # load 8 teaching patients that each hide one problem (--answers: instructor key)
```

---

## smart-app

Serve the patient dashboard at `http://localhost:8765/index.html` and open it in your browser. One UI for several EHRs, none needing a login: Cerner and HAPI are open, and Epic goes through a local read-only proxy that signs in with your Backend Systems app (`.env`, `keys/`).

```bash
pixi run smart-app                    # EHR from EHR_TYPE (else Cerner)
pixi run smart-app --ehr hapi         # cerner | epic | hapi
python cli.py smart-app --no-open     # don't open a browser
python cli.py smart-app --console     # also open the EHR's developer portal
pixi run smart-app --ehr hapi --keep-hapi   # leave the local HAPI server running on exit
```

With `--ehr hapi` the local HAPI server ([Local HAPI Server](setup/local-hapi.md)) is started if needed and stopped on Ctrl-C.

`--ehr` is only the starting point; the page has an EHR dropdown. See [Demo 3](demos/smart-app.md).

---

## smart-setup

Optional, Cerner only. Prints the exact values to enter when registering the app in code Console, prompts for the client ID, saves it to `smart-app/config.local.js` (gitignored) and checks the sandbox is reachable. Registration itself is manual. `--ehr epic` only reports whether your Epic backend app is configured; Epic needs no registration for the dashboard.

```bash
pixi run smart-setup --ehr cerner
python cli.py smart-setup --ehr cerner --client-id <id> --no-open
pixi run smart-setup --ehr epic     # just checks the backend app config
```

---

## generate-keys

Generate a new RSA key pair for Epic backend authentication.

```bash
pixi run generate-keys
```

If key files already exist, you will be prompted before anything is overwritten:

```
Existing key files found: private_key.pem, public_key.pem, public_jwks.json, public_jwk.json
Overwrite? [y/N]
```

To skip the prompt:

```bash
pixi run generate-keys-force
python cli.py generate-keys --force
```

The script also lives at `keys/generate_keys.py` and can be run directly:

```bash
python keys/generate_keys.py [--force]
```

See [Setup → Keys](setup/keys.md) for next steps after generation.

---

## codex-setup

Point OpenAI Codex at the course proxy and store your **OpenAI Token** (Windows, macOS, Linux, WSL).

```bash
pixi run codex-setup [<openai-token>]
```

Omit the **OpenAI Token** to be prompted for it (input hidden). The command validates common mistakes and prints a quick verification check. See [OpenAI Codex](setup/codex.md).

---

## docs

Serve the Zensical documentation site locally.

```bash
pixi run docs
```

Opens at `http://localhost:8000`.



