"""Generate an RSA key pair for Epic backend system authentication.

Writes to the same directory (keys/):
  private_key.pem  — signs JWTs; keep secret, never commit
  public_key.pem   — PEM form of the public key (for reference)
  public_jwks.json — host at a public URL and register in the Epic portal
  public_jwk.json  — single JWK (for reference)

Run:
  pixi run generate-keys
  python keys/generate_keys.py
"""
import json
import base64
import uuid
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

KEYS_DIR = Path(__file__).parent


def b64url(n: int) -> str:
    return base64.urlsafe_b64encode(
        n.to_bytes((n.bit_length() + 7) // 8, "big")
    ).rstrip(b"=").decode()


def generate(force: bool = False) -> None:
    existing = [f for f in ("private_key.pem", "public_key.pem", "public_jwks.json", "public_jwk.json")
                if (KEYS_DIR / f).exists()]

    if existing and not force:
        print(f"Existing key files found: {', '.join(existing)}")
        answer = input("Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    private_key = rsa.generate_private_key(65537, 2048, default_backend())

    (KEYS_DIR / "private_key.pem").write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )

    pub = private_key.public_key()
    (KEYS_DIR / "public_key.pem").write_bytes(
        pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )

    nums = pub.public_numbers()
    kid  = str(uuid.uuid4())
    jwk  = {"kty": "RSA", "use": "sig", "alg": "RS384", "kid": kid,
             "n": b64url(nums.n), "e": b64url(nums.e)}

    (KEYS_DIR / "public_jwk.json").write_text(json.dumps(jwk, indent=2))
    (KEYS_DIR / "public_jwks.json").write_text(json.dumps({"keys": [jwk]}, indent=2))

    print(f"Keys written to {KEYS_DIR}/")
    print(f"  kid: {kid}")
    print()
    print("Next steps:")
    print("  1. Update your GitHub Gist with the contents of keys/public_jwks.json")
    print("  2. In the Epic portal, remove and re-add the Non-Production JWK Set URL")
    print("  3. Click Save & Ready for Sandbox")


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    generate(force=force)
