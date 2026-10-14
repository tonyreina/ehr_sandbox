# Prerequisites

## Supported platforms

| Platform | Identifier |
|---|---|
| Linux (x86-64) | `linux-64` |
| Windows (x86-64) | `win-64` |
| macOS Intel | `osx-64` |
| macOS Apple Silicon | `osx-arm64` |

All platforms are declared in `pixi.toml` — no manual configuration needed.

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

## Python packages

Declared in `pixi.toml`, installed automatically by `pixi install`:

| Package | Purpose |
|---|---|
| `python-dotenv` | Load credentials from `.env` |
| `requests` | HTTP calls to the FHIR API |
| `pyjwt` | Sign JWTs for client credentials auth |
| `cryptography` | RSA key generation |
| `typer` | CLI framework |
| `fhirclient` | FHIR model helpers |

```bash
pixi install
```
