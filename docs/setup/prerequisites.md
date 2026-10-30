# Prerequisites

## Supported platforms

| Platform | Identifier |
|---|---|
| Linux (x86-64) | `linux-64` |
| Windows (x86-64) | `win-64` |
| macOS Intel | `osx-64` |
| macOS Apple Silicon | `osx-arm64` |

## Tools

Install these three tools, then get the project. All lessons use VS Code.

- **[VS Code](https://code.visualstudio.com/)** — the editor and terminal you will use for everything. Install it, then open the project folder with **File > Open Folder**. VS Code will offer to install the recommended extensions (Python and Docker); accept.

- **[pixi](https://pixi.sh)** — manages the Python environment and all dependencies. Run the command below in the VS Code terminal (**Terminal > New Terminal**), then close and reopen VS Code so it can find `pixi`.

    === "Linux / macOS"
        ```bash
        curl -fsSL https://pixi.sh/install.sh | bash
        ```
    === "Windows (PowerShell)"
        ```powershell
        iwr -useb https://pixi.sh/install.ps1 | iex
        ```

- **[Docker](https://docs.docker.com/get-docker/)** — runs the local HAPI patient server (`pixi run hapi-up`). It is not needed for the Cerner or Epic sandboxes, but the lessons use the local server.

    === "Windows / macOS"
        Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), start it, and wait until it says it is running. On Windows the installer also sets up WSL 2; restart if it asks.
    === "Ubuntu / Linux"
        Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/), then let your user run it without `sudo`, and log out and back in:

        ```bash
        sudo usermod -aG docker $USER
        ```

    Check that it works in the VS Code terminal:

    ```bash
    docker --version
    docker ps
    ```

    If `docker ps` says it cannot connect, Docker is installed but not running. Start Docker Desktop (or `sudo systemctl start docker` on Linux).

Pixi cannot install VS Code or Docker for you, and VS Code extensions cannot either: the Docker extension only manages Docker once it is installed.

## Get the project

Either download the project as a ZIP and unzip it, or clone it:

- **ZIP:** on [github.com/tonyreina/ehr_sandbox](https://github.com/tonyreina/ehr_sandbox) click **Code > Download ZIP**, unzip it, and open the folder in VS Code.
- **Git:** `git clone https://github.com/tonyreina/ehr_sandbox.git`

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



