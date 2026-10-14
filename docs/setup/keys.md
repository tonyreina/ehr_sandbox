# Generating RSA Keys

Epic backend system apps authenticate using a signed JWT. You generate an RSA key pair locally — the private key signs your tokens, the public key is hosted so Epic can verify them.

## Generate the key pair

```bash
pixi run generate-keys
```

If keys already exist, you'll be asked before anything is overwritten. To skip the prompt:

```bash
pixi run generate-keys-force
```

This writes four files to `keys/`:

| File | Committed | Description |
|---|---|---|
| `private_key.pem` | No | Signs JWTs — keep secret, never share |
| `public_key.pem` | No | PEM form of the public key (reference only) |
| `public_jwks.json` | Yes | JWKS format — host this at a public URL |
| `public_jwk.json` | Yes | Single JWK (reference only) |

The command also prints the `kid` (key ID) and next steps.

## Host the public key

Create a [GitHub Gist](https://gist.github.com):

1. Filename: `jwks.json`
2. Paste the contents of `keys/public_jwks.json`
3. Click **Create public gist** → **Raw**
4. Copy the raw URL — you'll need it when registering the app in Epic

!!! warning "Rotating keys"
    If you run `generate-keys` again, a new private key is created. You must:

    1. Update your Gist with the new `keys/public_jwks.json`
    2. Remove and re-add the JWKS URL in the Epic portal
    3. Click **Save & Ready for Sandbox**
