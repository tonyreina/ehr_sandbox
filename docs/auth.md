# Authentication

This page covers **Epic** backend authentication. Other backends:

- **Cerner open sandbox** (`EHR_TYPE=cerner`): no authentication.
- **Dashboard sign-in (Cerner and Epic)**: OAuth 2.0 authorization code flow with a user login, handled by `fhirclient` in the browser. See [Browser sign-in](#browser-sign-in-smart-on-fhir).
- **HAPI** (`EHR_TYPE=hapi`): no authentication.

---

Epic backend system apps use the **OAuth 2.0 client credentials** flow with a signed JWT assertion. No user login is required. This is implemented in `ehr/epic.py` (`EpicClient`).

## Flow

```mermaid
sequenceDiagram
    autonumber
    participant App as Your app (EpicClient)
    participant Auth as Epic token endpoint
    participant JWKS as Your JWKS URL (raw.githubusercontent.com)
    participant FHIR as Epic FHIR API

    App->>App: Sign JWT with private key (RS384)
    App->>Auth: POST client_credentials + signed JWT
    Auth->>JWKS: Fetch public keys
    JWKS-->>Auth: JWKS (matched by kid)
    Auth-->>App: Access token (1 hour)
    App->>FHIR: GET /Patient/{id} with Bearer token
    FHIR-->>App: FHIR resource
```

## JWT claims

| Claim | Value |
|---|---|
| `iss` | Your Non-Production Client ID |
| `sub` | Your Non-Production Client ID |
| `aud` | Token endpoint URL |
| `jti` | Random UUID (prevents replay) |
| `iat` | Current Unix timestamp |
| `exp` | `iat + 300` (5 minutes max) |

The JWT header must include `"kid"` matching a key in your hosted JWKS.

## Token caching

`EpicClient` caches the access token and only re-fetches it 60 seconds before expiry (tokens are valid for 1 hour). Calling `ClientFactory.from_env()` multiple times within a request does not trigger redundant token requests.

```mermaid
flowchart TD
    A[FHIR call requested] --> B{"Token cached and more than 60 s from expiry?"}
    B -- yes --> D[Send request with cached token]
    B -- no --> C[Sign JWT and request a new token]
    C --> E[Cache token and expiry]
    E --> D
```

## Browser sign-in (SMART on FHIR)

The browser dashboard's signed-in mode uses the **authorization code** flow with a user login, not client credentials (a browser can't hold the backend private key). `fhirclient` discovers the endpoints from `.well-known/smart-configuration`, so none are hard-coded. Setup: [Cerner Account & Registration](setup/cerner-account.md), [Epic SMART App Registration](setup/epic-smart-app.md).

**EHR launch (Cerner Provider app):** the EHR starts the app.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Console as code Console
    participant App as Dashboard (browser)
    participant Auth as Cerner authorization server
    participant FHIR as Cerner FHIR API (fhir-ehr-code)

    User->>Console: Test Sandbox, pick patient, Launch
    Console->>App: launch.html?iss=...&launch=...
    App->>FHIR: GET .well-known/smart-configuration
    FHIR-->>App: authorize and token endpoints
    App->>Auth: Redirect with client_id, scope, aud, state
    Auth->>User: Sign in with test credentials
    Auth->>App: Redirect to index.html?code=...&state=...
    App->>Auth: POST code for token
    Auth-->>App: Access token (about 10 minutes)
    App->>FHIR: GET Patient and Observation with Bearer token
    FHIR-->>App: FHIR resources
```

**Standalone launch (Epic):** the dashboard starts the login itself, once, using the `launch/patient` scope.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as Dashboard (browser)
    participant Auth as Epic authorization server
    participant FHIR as Epic FHIR API

    User->>App: pixi run smart-app --ehr epic
    App->>FHIR: GET .well-known/smart-configuration
    FHIR-->>App: authorize and token endpoints
    App->>Auth: Redirect with client_id, launch/patient scope, aud, state, PKCE challenge
    Auth->>User: Sign in as a sandbox test patient
    Auth->>App: Redirect to index.html?code=...&state=...
    App->>Auth: POST code and PKCE verifier for token
    Auth-->>App: Access token and the patient id
    App->>FHIR: GET Patient and Observation with Bearer token
    FHIR-->>App: FHIR resources
```

## Using the client

```python
from ehr import ClientFactory

client = ClientFactory.from_env()           # reads EHR_TYPE from .env
patient = client.get_patient("erXuFYUfucBZaryVksYEcMg3")
obs     = client.get_observations("erXuFYUfucBZaryVksYEcMg3", category="laboratory")
```

## Adding a new EHR

See [EHR Clients → Adding a new backend](ehr-clients.md#adding-a-new-backend).
