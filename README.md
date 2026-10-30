# FHIR Sandbox

Python demos and a browser dashboard for FHIR R4 sandboxes: the Oracle Health (Cerner) open sandbox, the Epic sandbox and a local HAPI FHIR server.

![Patient dashboard on the Oracle Health (Cerner) open sandbox](docs/demos/oracle_ehr_app.png)

Based on the blog post [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/).

## Install

Requires [pixi](https://pixi.sh).

```bash
git clone https://github.com/tonyreina/ehr_sandbox.git
cd ehr_sandbox
pixi install
pixi run smart-app        # patient dashboard: http://localhost:8765/index.html
```

No account is needed for the default Cerner open sandbox.

## Set up OpenAI Codex (course users)

Point Codex at the course proxy and store your **OpenAI Token** (works in Windows PowerShell, macOS, Ubuntu and WSL):

```bash
pixi run codex-setup <openai-token>
```

Then fully quit and reopen VS Code. Omit the **OpenAI Token** to be prompted for it. Run it inside WSL if you use a WSL window in VS Code. Details: [OpenAI Codex setup](https://tonyreina.github.io/ehr_sandbox/setup/codex/).

## Documentation

Setup for Epic and Cerner, authentication, the dashboard, CLI reference and test patients:

**https://tonyreina.github.io/ehr_sandbox/**

To read it locally, run `pixi run docs`.



