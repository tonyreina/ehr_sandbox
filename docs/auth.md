# Authentication

Epic backend system apps use the **OAuth 2.0 client credentials** flow with a signed JWT assertion. No user login is required.

## Flow

```
Your app                     Epic token endpoint
   |                               |
   |-- signed JWT (RS384) -------> |
   |                               | (fetches JWKS URL, verifies signature)
   |<-- access token (1 hour) ---- |
   |                               |
   |-- Bearer <token> -----------> Epic FHIR API
   |<-- FHIR resource ------------ |
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

## epic_auth.py

The `epic_auth.py` module handles token acquisition automatically:

```python
from epic_auth import authed_session

session = authed_session()
response = session.get(f"{FHIR_BASE}/Patient/{patient_id}")
```

`authed_session()` returns a `requests.Session` with the `Authorization: Bearer` header pre-set.
