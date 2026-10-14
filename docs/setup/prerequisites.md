# Prerequisites

## Tools

- **[pixi](https://pixi.sh)** — handles the Python environment and dependencies. Install with:
  ```bash
  curl -fsSL https://pixi.sh/install.sh | bash
  ```
- A **GitHub account** (to host your public JWK Set as a Gist)
- An **Epic developer account** at [fhir.epic.com](https://fhir.epic.com)

## Python packages

These are declared in `pixi.toml` and installed automatically:

| Package | Purpose |
|---|---|
| `python-dotenv` | Load credentials from `.env` |
| `requests` | HTTP calls to the FHIR API |
| `pyjwt` | Sign JWTs for client credentials auth |
| `cryptography` | RSA key generation |
| `fhirclient` | FHIR model helpers |

Install everything with:

```bash
pixi install
```
