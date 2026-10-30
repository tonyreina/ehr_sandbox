# Prerequisites

## Supported platforms

| Platform | Identifier |
|---|---|
| Linux (x86-64) | `linux-64` |
| Windows (x86-64) | `win-64` |
| macOS Intel | `osx-64` |
| macOS Apple Silicon | `osx-arm64` |

## Tools

- **[pixi](https://pixi.sh)** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â manages the Python environment and all dependencies.

    === "Linux / macOS"
        ```bash
        curl -fsSL https://pixi.sh/install.sh | bash
        ```
    === "Windows (PowerShell)"
        ```powershell
        iwr -useb https://pixi.sh/install.ps1 | iex
        ```

Depending on the backend you want to use:

- **Cerner (Oracle Health) open sandbox:** nothing else. No account needed. See [Cerner Sandbox](cerner-sandbox.md).
- **Cerner signed-in SMART mode (optional):** a CernerCare account for code Console. See [Cerner Account & Registration](cerner-account.md).
- **Epic in the browser dashboard:** nothing extra; it reuses the backend app. See [Epic in the Dashboard](epic-dashboard.md).
- **Epic:** an **Epic developer account** at [fhir.epic.com](https://fhir.epic.com) and a **GitHub account** (to host your public JWK Set at a `raw.githubusercontent.com` URL; see [Keys](keys.md)).

## Installation

```bash
pixi install
```

This installs all conda-forge packages **and** the `ehr` package itself as an editable install (via `pyproject.toml`), so changes to `ehr/` take effect immediately without reinstalling.

## OpenAI Codex (course users)

After `pixi install`, configure Codex with your **OpenAI Token**:

```bash
pixi run codex-setup <openai-token>
```

Then fully quit and reopen VS Code. See [OpenAI Codex](codex.md) for what it changes, verification, and WSL notes.

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



