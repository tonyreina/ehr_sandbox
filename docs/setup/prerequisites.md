# Prerequisites

## Supported platforms

| Platform | Identifier |
|---|---|
| Linux (x86-64) | `linux-64` |
| Windows (x86-64) | `win-64` |
| macOS Intel | `osx-64` |
| macOS Apple Silicon | `osx-arm64` |

## Tools

- **[pixi](https://pixi.sh)** — manages the Python environment and all dependencies.

    === "Linux / macOS"
        ```bash
        curl -fsSL https://pixi.sh/install.sh | bash
        ```
    === "Windows (PowerShell)"
        ```powershell
        iwr -useb https://pixi.sh/install.ps1 | iex
        ```

- A **GitHub account** (to host your public JWK Set as a Gist)
- An **Epic developer account** at [fhir.epic.com](https://fhir.epic.com)

## Installation

```bash
pixi install
```

This installs all conda-forge packages **and** the `ehr` package itself as an editable install (via `pyproject.toml`), so changes to `ehr/` take effect immediately without reinstalling.

## Python packages

| Package | Purpose |
|---|---|
| `python-dotenv` | Load credentials from `.env` |
| `requests` | HTTP calls to the FHIR API |
| `pyjwt` | Sign JWTs for client credentials auth |
| `cryptography` | RSA key generation |
| `typer` | CLI framework |
| `fhirclient` | FHIR model helpers |
| `zensical` | Documentation site generator |
| `hatchling` | Build backend for the editable install |
