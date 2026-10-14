# Epic FHIR Sandbox

Python demos for querying the Epic FHIR R4 sandbox using backend system (client credentials) OAuth 2.0 authentication.

These demos implement the patterns from [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/) and connect to Epic's public open sandbox at `fhir.epic.com`.

## What you can do

- **Demo 1** — Retrieve patient demographics by FHIR ID
- **Demo 2** — Query laboratory observations for a patient

## Quick start

```bash
pixi run python demo_01_patient.py camila
pixi run python demo_02_observations.py theodore
```

See [Setup](setup/prerequisites.md) for full installation instructions.
