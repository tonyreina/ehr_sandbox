# Epic Portal Configuration

## Create the app

1. Go to [fhir.epic.com](https://fhir.epic.com) and sign in
2. Click **Build Apps** → **Create App**
3. Set **Application Audience** to **Backend Systems**
4. Set **Use Case** to **General**

## Select incoming APIs

Search for and add to **Selected**:

- `Patient.Read (Demographics R4)`
- `Patient.Search (Demographics R4)`
- `Observation.Search (Outside Record)`
- `Observation.Read (Outside Record)`

## Register your public key

In the **Non-Production JWK Set URL** field, paste the raw GitHub Gist URL for your `keys/public_jwks.json`. Epic will validate it is reachable and show **Validated**.

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
