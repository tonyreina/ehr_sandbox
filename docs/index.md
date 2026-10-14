# Epic FHIR Sandbox

Python demos for querying the Epic FHIR R4 sandbox using backend system (client credentials) OAuth 2.0 authentication.

Based on [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/).

## What you can do

- **`patient`** — Retrieve patient demographics by name
- **`observations`** — Query laboratory (or other) observations
- **`generate-keys`** — Generate a new RSA key pair for Epic auth
- **`list-patients`** — Show all known sandbox test patients

## Quick start

```bash
pixi run patient camila
pixi run observations theodore
pixi run list-patients
```

See [Setup → Prerequisites](setup/prerequisites.md) for installation, or [CLI](cli.md) for the full command reference.
