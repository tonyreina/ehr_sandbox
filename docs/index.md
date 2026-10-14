# Epic FHIR Sandbox

Python demos for querying FHIR R4 servers using backend system (client credentials) OAuth 2.0 authentication.

The project is built around a multi-EHR abstraction layer — swap `EHR_TYPE` in `.env` to target a different server without changing any code.

Based on [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/).

## Supported EHR backends

| `EHR_TYPE` | Status | Auth |
|---|---|---|
| `epic` | Full | JWT client credentials (RS384) |
| `cerner` | Stub | JWT client credentials (RS384) |
| `hapi` | Full | None (local dev) |

## Available commands

```bash
pixi run patient [camila|derrick|theodore|linda]
pixi run observations [name] [--category vital-signs] [--count 10]
pixi run list-patients
pixi run list-ehrs
pixi run generate-keys
```

See [Setup → Prerequisites](setup/prerequisites.md) to get started, or [EHR Clients](ehr-clients.md) for the architecture.
