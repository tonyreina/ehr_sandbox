# FHIR Sandbox

Practice with realistic synthetic patients: look at a chart in your browser, then ask an AI about it and check its answers. No coding needed.

![Patient dashboard](docs/demos/hapi_ehr_app.png)

## Start

1. Install [VS Code](https://code.visualstudio.com/), [pixi](https://pixi.sh) and [Docker](https://docs.docker.com/get-docker/), then download this project (**Code > Download ZIP** and unzip it) and open it in VS Code.
2. In the VS Code terminal (**Terminal > New Terminal**) install the project and save your token:

```bash
pixi install
pixi run codex-setup <your-token>
```

3. Fully restart VS Code, then check the token (it should end with `Result: OK`) and start the practice patients and the dashboard:

```bash
pixi run codex-check
pixi run hapi-up
pixi run hapi-load
pixi run hapi-scenarios
pixi run smart-app --ehr hapi
```

Step-by-step guide with screenshots: **https://tonyreina.github.io/ehr_sandbox/** (or `pixi run docs`). Based on [FHIR Practical Interoperability](https://www.doctorswhocode.blog/blog/fhir-practical-interoperability/). Epic and Oracle Health (Cerner) sandboxes are covered under Advanced in the docs.

## Development

Tests need a developer environment that learners do not install:

```bash
pixi run -e dev install-browser   # once: downloads Chromium for Playwright
pixi run -e dev ui-test           # dashboard test against a fake FHIR server
pixi run ask-test                 # the Ask box's proxy client against a mock proxy
```
