"""Epic backend system JWT auth — gets a bearer token using the client credentials flow."""
import os
import uuid
import time
import json
import jwt
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

CLIENT_ID  = os.getenv('EPIC_CLIENT_ID')
TOKEN_URL  = os.getenv('EPIC_TOKEN_URL')
FHIR_BASE  = os.getenv('EPIC_FHIR_BASE')
KEY_FILE   = os.path.join(os.path.dirname(__file__), 'keys', 'private_key.pem')
JWKS_FILE  = os.path.join(os.path.dirname(__file__), 'keys', 'public_jwks.json')


def _kid() -> str:
    with open(JWKS_FILE) as f:
        return json.load(f)['keys'][0]['kid']


def get_access_token() -> str:
    with open(KEY_FILE, 'rb') as f:
        private_key = f.read()

    now = int(time.time())
    claims = {
        'iss': CLIENT_ID,
        'sub': CLIENT_ID,
        'aud': TOKEN_URL,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + 300,
    }

    signed_jwt = jwt.encode(claims, private_key, algorithm='RS384',
                            headers={'kid': _kid()})

    resp = requests.post(TOKEN_URL, data={
        'grant_type':            'client_credentials',
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion':      signed_jwt,
    })
    resp.raise_for_status()
    return resp.json()['access_token']


def authed_session() -> requests.Session:
    token = get_access_token()
    s = requests.Session()
    s.headers.update({
        'Authorization': f'Bearer {token}',
        'Accept':        'application/fhir+json',
    })
    return s
