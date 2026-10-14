# CLI Reference

All commands are available as pixi tasks (recommended) or by running `python cli.py` directly.

## patient

Fetch and display demographics for a sandbox test patient.

```bash
pixi run patient [camila|derrick|theodore|linda]
```

Default patient: `camila`.

**Example:**

```
$ pixi run patient derrick
Patient: Derrick Lin
DOB:     1973-06-03
Gender:  male
ID:      eq081-VQEgP8drUUqCWzHfw3
```

---

## observations

Fetch observations for a patient. Defaults to laboratory results.

```bash
pixi run observations [name] [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--category` | `laboratory` | Observation category (`vital-signs`, `imaging`, etc.) |
| `--count`, `-n` | `20` | Maximum number of results |

**Examples:**

```bash
pixi run observations theodore
pixi run observations camila --category vital-signs
pixi run observations linda --count 5
```

---

## list-patients

Print a table of all known sandbox test patients.

```bash
pixi run list-patients
```

```
Key          Name                 DOB          Sex  FHIR ID
-----------------------------------------------------------
camila       Camila Lopez         1987-09-12   F    erXuFYUfucBZaryVksYEcMg3
derrick      Derrick Lin          1973-06-03   M    eq081-VQEgP8drUUqCWzHfw3
theodore     Theodore Mychart     1948-07-07   M    e63wRTbPfr1p8UW81d8Seiw3
linda        Linda Ross           1969-04-27   F    eIXesllypH3M9tAA5WdJftQ3
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

To skip the prompt (e.g. in CI or scripted rotation):

```bash
pixi run generate-keys-force
# or
python cli.py generate-keys --force
```

The script lives at `keys/generate_keys.py` and can also be run directly:

```bash
python keys/generate_keys.py [--force]
```

Writes to `keys/`. See [Generating RSA Keys](setup/keys.md) for details and next steps.

---

## docs

Serve the Zensical documentation site locally.

```bash
pixi run docs
```

Opens at `http://localhost:8000`.
