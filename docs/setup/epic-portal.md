# Epic Portal Configuration

## Create the app

1. Go to [fhir.epic.com](https://fhir.epic.com) and sign in
2. Click **Build Apps** → **Create App**
3. Set **Application Audience** to **Backend Systems**
4. Set **Use Case** to **General**

## Select incoming APIs

Search for each API by name and add it to **Selected**. Add only what you use: every API is another permission you grant the app.

### Required (Python demos)

- `Patient.Read (Demographics R4)`
- `Patient.Search (Demographics R4)`
- `Observation.Search (Outside Record)`
- `Observation.Read (Outside Record)`

### Dashboard sections

The dashboard in `pixi run smart-app --ehr epic` shows these sections only if the matching search API is selected:

| Dashboard section | API to add |
|---|---|
| Medications | `MedicationRequest.Search` (signed medication order, R4) |
| Allergies | `AllergyIntolerance.Search` (R4) |
| Encounters | `Encounter.Search` (R4) |
| Problems | `Condition.Search` (Problems, R4) |

Epic splits `Observation` into separate APIs for labs, vitals and social history. If vital signs, labs or `--category social-history` come back empty, add the matching `Observation.Search` variant.

### Optional (AI lectures)

- `DocumentReference.Search` and `Binary.Read`: clinical notes and their text, the data a language model reads best.
- `DiagnosticReport.Search`: results and reports.
- `Procedure.Search` and `Immunization.Search`: for "is this patient due for anything?" questions.
- `CarePlan.Search` and `Goal.Search`: care plans and goals.
- `Practitioner.Read`, `Location.Read` and `Organization.Read`: turn IDs in other resources into names.

!!! note
    Epic's exact API names and the variants offered (Patient Chart, Outside Record, and so on) change over time. Search the portal for the resource name and pick the R4 entry that matches. Sandbox test patients have sparse data, so a new API does not guarantee results for every patient.

## Register your public key

In the **Non-Production JWK Set URL** field, paste:

```
https://raw.githubusercontent.com/tonyreina/ehr_sandbox/main/keys/public_jwks.json
```

Epic will validate it is reachable and show **Validated**.

## Activate for sandbox

Click **Save & Ready for Sandbox** at the bottom of the page. Your **Non-Production Client ID** (shown at the top) is the value to put in `.env`.

!!! note
    Newly added API permissions can take up to an hour to propagate in the sandbox after clicking Save & Ready for Sandbox.

## Environment file

```
EPIC_CLIENT_ID=<your-non-production-client-id>
EPIC_FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

## Using it in the dashboard

The same app powers Epic in the browser dashboard: `pixi run smart-app --ehr epic` signs in with it server-side. See [Epic in the Dashboard](epic-dashboard.md). To show medications, allergies, encounters and problems there, also add the APIs listed under [Dashboard sections](#dashboard-sections).
