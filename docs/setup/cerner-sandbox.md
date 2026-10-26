# Cerner (Oracle Health) Sandbox

The Oracle Health **open sandbox** is a public, read-only FHIR R4 endpoint. It needs no developer account, no app registration and no keys, so it is the quickest way to try the demos.

## Configure

Set the backend in `.env`:

```
EHR_TYPE=cerner
```

That's all. The client defaults to the public sandbox tenant:

```
https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d
```

To target a different open tenant, override it:

```
CERNER_FHIR_BASE=https://fhir-open.cerner.com/r4/<tenant-id>
```

## Verify the endpoint

```bash
curl -H "Accept: application/fhir+json" \
  "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d/metadata"
```

## Try the dashboard

```bash
pixi run smart-app
```

opens a browser dashboard on the same open sandbox with no login. See [Demo 3](../demos/smart-app.md). For a signed-in SMART session see [Cerner Account & Registration](cerner-account.md).

## Run the demos

```bash
pixi run list-patients
pixi run patient nancy
pixi run observations joe
pixi run observations nancy --category vital-signs --count 5
```

## Test patients

| Key | Name | DOB | Sex | FHIR ID |
|---|---|---|---|---|
| `nancy` | Nancy Patchtest | 1990-01-02 | F | `12724066` |
| `joe` | Joe Testpatient | 1990-05 | M | `12724067` |
| `wilm` | Wilm Smart | 1990-09-15 | M | `12724065` |
| `tim` | Tim Peters | 1990-09-15 | M | `12742400` |

Any other FHIR ID can be passed directly, e.g. `pixi run patient 12724065`.

## Differences from Epic

- Names are upper-case in the sandbox (`NANCY PATCHTEST`).
- Birth dates can be partial (`1990-05`).
- The sandbox is shared and mutable; data and dates (including some far-future timestamps) change over time, so output will differ from the examples.
- Blood pressure observations carry `component` values rather than `valueQuantity`, so the demos' simple value printer skips them.
- Secured Cerner endpoints (SMART backend services with client credentials) are **not** implemented.
