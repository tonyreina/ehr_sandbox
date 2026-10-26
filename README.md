# FHIR Sandbox

Python demos and a browser dashboard for FHIR R4 sandboxes:

- **Oracle Health (Cerner)** open sandbox: no account, no login.
- **Epic** sandbox: backend system (client credentials) authentication.
- **HAPI FHIR** (local Docker): no authentication.

Select the backend for the Python demos with `EHR_TYPE` in `.env` (`cerner`, `epic` or `hapi`).

Based on the blog post [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/). Full documentation: `pixi run docs`.

## Quick start (no account needed)

Requires [pixi](https://pixi.sh).

```bash
pixi install
pixi run smart-app        # patient dashboard (Cerner, no login): http://localhost:8765/index.html
```

The dashboard shows vitals trend charts, labs, medications, allergies, encounters and problems for sandbox patients, with a patient picker and name search. See [docs/demos/smart-app.md](docs/demos/smart-app.md).

For the command-line demos against the same Cerner sandbox, set `EHR_TYPE=cerner` in `.env`, then:

```bash
pixi run list-patients
pixi run patient nancy
pixi run observations joe
pixi run observations nancy --category vital-signs --count 5
```

## Patient dashboard: one UI, several EHRs

`smart-app/` is a browser dashboard (vitals charts, labs, medications, allergies, encounters, problems) with an EHR dropdown. None of them needs a login: Cerner and HAPI are open, and Epic goes through a local proxy that uses your existing Backend Systems app (`.env`, `keys/`). See [docs/demos/smart-app.md](docs/demos/smart-app.md).

```bash
pixi run smart-app                 # Cerner open sandbox, no login (default)
pixi run smart-app --ehr hapi      # public HAPI server, no login
pixi run smart-app --ehr epic      # via your Epic backend app (see Epic setup below)
```

Optional signed-in Cerner SMART session: `pixi run smart-setup --ehr cerner` prints the values to enter in code Console and saves the client ID ([step-by-step](docs/setup/cerner-account.md)); registration is manual because Oracle provides no API for it. Epic in the dashboard: [docs/setup/epic-dashboard.md](docs/setup/epic-dashboard.md).

## Epic setup (optional)

Needs an Epic sandbox app registered at [fhir.epic.com](https://fhir.epic.com) with:

- Application audience: **Backend Systems**
- Incoming APIs: `Patient.Read (Demographics R4)`, `Observation.Search (Outside Record)`
- Non-production JWK Set URL pointing to your hosted `keys/public_jwks.json`
- Status: **Saved & Ready for Sandbox**

Then:

```bash
pixi run generate-keys    # creates keys/ (private key stays local and gitignored)
```

Create `.env`:

```bash
EHR_TYPE=epic
EPIC_CLIENT_ID=your-non-production-client-id
EPIC_FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

Host `keys/public_jwks.json` at a **`raw.githubusercontent.com`** URL (a Gist URL caused `invalid_client` even with correct keys), paste it into the app's **Non-Production JWK Set URL**, and click **Save & Ready for Sandbox**. Details: [docs/setup/keys.md](docs/setup/keys.md) and [docs/setup/epic-portal.md](docs/setup/epic-portal.md).

## Commands

```bash
pixi run smart-app [--ehr cerner|epic|hapi]   # patient dashboard
pixi run smart-setup --ehr cerner             # optional: signed-in Cerner SMART session
pixi run patient [name]                  # keys depend on EHR_TYPE
pixi run observations [name] [--category vital-signs] [--count 10]
pixi run list-patients                   # test patients for the active EHR
pixi run list-ehrs                       # registered backends
pixi run generate-keys                   # Epic key pair
pixi run docs                            # serve the documentation site
```

## Test patients

| EHR | Keys |
|---|---|
| Cerner | `nancy` (12724066), `joe` (12724067), `wilm` (12724065), `tim` (12742400) |
| Epic | `camila`, `derrick`, `theodore`, `linda` |

Any other FHIR ID can be passed directly, e.g. `pixi run patient 12724065`. Run `pixi run list-patients` for the full table.

## Project structure

```
epic_sandbox/
├── ehr/                     # multi-EHR client package
│   ├── base.py              # BaseEHRClient interface
│   ├── factory.py           # ClientFactory (selects by EHR_TYPE)
│   ├── epic.py              # Epic: JWT client credentials (RS384)
│   ├── cerner.py            # Cerner: open sandbox, no auth
│   ├── hapi.py              # HAPI: local, no auth
│   └── patients.py          # test patients per EHR
├── demos/                   # demo_01_patient.py, demo_02_observations.py
├── smart-app/               # browser dashboard: Cerner, Epic, HAPI profiles
├── keys/                    # Epic key generation (private key gitignored)
├── docs/                    # Zensical documentation source
├── cli.py                   # Typer CLI (all pixi tasks point here)
├── .env                     # gitignored: backend choice and credentials
├── pixi.toml                # dependencies and task shortcuts
└── zensical.toml            # docs site config
```
