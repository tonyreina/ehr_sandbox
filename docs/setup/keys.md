# Generating RSA Keys

Epic backend system apps authenticate using a signed JWT. You generate an RSA key pair locally — the private key signs your tokens, the public key is hosted so Epic can verify them.

## Generate the key pair

```bash
pixi run python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import json, base64, uuid

key = rsa.generate_private_key(65537, 2048, default_backend())

with open('keys/private_key.pem', 'wb') as f:
    f.write(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

pub = key.public_key().public_numbers()
def b64(n): return base64.urlsafe_b64encode(n.to_bytes((n.bit_length()+7)//8,'big')).rstrip(b'=').decode()

jwks = {'keys': [{'kty':'RSA','use':'sig','alg':'RS384','kid':str(uuid.uuid4()),'n':b64(pub.n),'e':b64(pub.e)}]}
with open('keys/public_jwks.json', 'w') as f:
    json.dump(jwks, f, indent=2)
print('Done')
"
```

This writes two files:

| File | Description |
|---|---|
| `keys/private_key.pem` | **Keep secret.** Never commit. Signs your JWTs. |
| `keys/public_jwks.json` | **Host publicly.** Epic fetches this to verify your signatures. |

Both are gitignored by default.

## Host the public key

Create a [GitHub Gist](https://gist.github.com):

1. Filename: `jwks.json`
2. Paste the contents of `keys/public_jwks.json`
3. Click **Create public gist** → **Raw**
4. Copy the raw URL — you'll need it in the next step

!!! warning
    If you regenerate the key pair, you must update the Gist **and** re-save the JWKS URL in the Epic portal to force Epic to re-fetch the new public key.
