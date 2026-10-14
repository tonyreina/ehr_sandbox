# Epic FHIR Sandbox

Python demos for the Epic FHIR R4 sandbox using backend system (client credentials) authentication.

Based on the blog post [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/).

## Prerequisites

- [pixi](https://pixi.sh) package manager
- An Epic sandbox app registered at [fhir.epic.com](https://fhir.epic.com) with:
  - Application audience: **Backend Systems**
  - Incoming APIs: `Patient.Read (Demographics R4)`, `Observation.Search (Outside Record)`
  - Non-production JWK Set URL pointing to your hosted `keys/public_jwks.json`
  - Status: **Saved & Ready for Sandbox**

## Setup

**1. Install dependencies**

```bash
pixi install
```

**2. Configure environment**

Copy `.env` and fill in your credentials:

```bash
EPIC_CLIENT_ID=your-non-production-client-id
EPIC_FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

**3. Generate RSA keys**

```bash
pixi run generate-keys
```

**4. Register the public key with Epic**

Host `keys/public_jwks.json` at a public URL (e.g. a GitHub Gist raw URL) and paste it into the **Non-Production JWK Set URL** field of your Epic app, then click **Save & Ready for Sandbox**.

## Running the demos

```bash
pixi run patient [camila|derrick|theodore|linda]
pixi run observations [name] [--category vital-signs] [--count 10]
pixi run list-patients
pixi run generate-keys
```

## Known sandbox test patients

| Name | DOB | Gender | FHIR ID |
|---|---|---|---|
| Camila Lopez | 1987-09-12 | F | `erXuFYUfucBZaryVksYEcMg3` |
| Derrick Lin | 1973-06-03 | M | `eq081-VQEgP8drUUqCWzHfw3` |
| Theodore Mychart | 1948-07-07 | M | `e63wRTbPfr1p8UW81d8Seiw3` |
| Linda Ross | 1969-04-27 | F | `eIXesllypH3M9tAA5WdJftQ3` |

## Project structure

```
epic_sandbox/
├── keys/
│   ├── generate_keys.py     # key generation script (run via pixi)
│   ├── private_key.pem      # gitignored — keep secret
│   ├── public_key.pem       # gitignored
│   ├── public_jwks.json     # host this at a public URL for Epic
│   └── public_jwk.json      # single JWK (reference)
├── docs/                    # Zensical documentation source
├── demo_01_patient.py       # fetch patient demographics
├── demo_02_observations.py  # fetch lab results
├── cli.py                   # Typer CLI (all pixi tasks point here)
├── epic_auth.py             # JWT client-credentials auth helper
├── .env                     # gitignored — your client ID and URLs
├── pixi.toml                # dependency management + task shortcuts
└── zensical.toml            # docs site config
```
