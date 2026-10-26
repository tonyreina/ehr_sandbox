# Epic SMART App Registration

The Python demos use Epic **backend** authentication (a signed JWT, see [Epic Portal](epic-portal.md)). The browser dashboard can't use that: a browser can't keep a private key. For the dashboard Epic needs a separate, **patient-facing SMART app** registered as a public client. It is used only for `pixi run smart-app --ehr epic`.

!!! note "Verification status"
    The dashboard's Epic path is tested against a mocked Epic only. The field names below are Epic's as best known and may differ in the portal; if one doesn't match, pick the closest option and tell us what to change.

## 1. Register the app

Sign in at [fhir.epic.com](https://fhir.epic.com) (the same developer account as the backend app), choose **Build Apps** → **Create**, and enter:

| Field | Value |
|---|---|
| Application Audience | **Patients** |
| SMART on FHIR Version | R4 |
| Confidential client | No (public client; PKCE) |
| Redirect URI | `http://localhost:8765/index.html` |
| Incoming APIs | `Patient.Read` (Demographics) R4, `Observation.Read` and `Observation.Search` (Labs, Vitals) R4 |

```bash
pixi run smart-setup --ehr epic
```

prints these values and opens the portal. Epic shows a **Non-Production Client ID** on the app page; copy it (not the production one).

Newly saved apps and API changes can take a while to reach the sandbox (up to about an hour for new APIs).

## 2. Save the client ID

```bash
pixi run smart-setup --ehr epic --client-id <non-production-client-id>
```

It is stored in `smart-app/config.local.js` (gitignored) next to any Cerner client ID. It is an identifier, not a secret.

## 3. Run

```bash
pixi run smart-app --ehr epic
```

The dashboard sees that Epic has no open endpoint and sends you to Epic's login on its own. Sign in with one of Epic's sandbox test patient accounts (their usernames and passwords are listed in Epic's *Sandbox test data* documentation at [fhir.epic.com/Documentation](https://fhir.epic.com/Documentation)). You return to the dashboard showing that patient.

## What to expect

- **One patient.** A patient login grants `patient/…` scopes, which only cover the patient who signed in, so the patient picker and search are hidden.
- **Other sections.** Only Patient and Observation are requested by default (vitals, labs). To show medications, allergies, encounters and problems, add their read APIs to the Epic app **and** add the resource names to `profiles.epic.resources` in `smart-app/config.js`; until then those sections show *Not authorized*. Epic also needs particular search parameters for some of them, so a section can still be empty or unavailable.
- **No loop.** The automatic redirect to Epic happens once per browser session. If the login is cancelled or fails, the dashboard shows the error and a **Sign in** button.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| *No Epic client id yet* | Run `pixi run smart-setup --ehr epic`. |
| Epic rejects the request with an `invalid_client`, redirect or scope error | The Redirect URI must be exactly `http://localhost:8765/index.html`, the app must be a patient-facing public client, and the requested scopes must match the APIs added to the app. |
| `403` or *Not authorized* in a section | That resource's API isn't on the Epic app or isn't in `profiles.epic.resources`. |
| The page shows Cerner or HAPI instead | Use the EHR dropdown, `?ehr=epic`, or `--ehr epic`. |
