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

## Documentation

Setup for Epic and Cerner, authentication, the dashboard, CLI reference and test patients:

**https://tonyreina.github.io/ehr_sandbox/**

To read it locally, run `pixi run docs`.
