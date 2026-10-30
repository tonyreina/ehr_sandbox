# Docs Notes

## Windows Codex setup (beginner-friendly)

If this is your first time using terminal commands, use these exact steps.

1. Open the **Start menu**.
2. Search for **PowerShell** and open it.
3. Copy and paste this command, then press **Enter**:

```powershell
pixi run codex-setup <openai-token>
```

4. Replace `<openai-token>` with your real **OpenAI Token**.

Example:

```powershell
pixi run codex-setup sk-abc123...
```

If you prefer not to include the **OpenAI Token** in the command:

```powershell
pixi run codex-setup
```

Then paste the **OpenAI Token** when prompted.

## What happens automatically

- `%USERPROFILE%\.codex\config.toml` is created/updated.
- API base URL is set to the course proxy endpoint automatically.
- `env_key = "OPENAI_TOKEN"` is set.
- Your **OpenAI Token** is saved as a Windows user environment variable (`OPENAI_TOKEN`).

## Final step

Completely close and reopen VS Code so it picks up the new **OpenAI Token**.

## Quick check

In a **new** PowerShell window, run:

```powershell
Get-Content ~\.codex\config.toml
$env:OPENAI_TOKEN
```

You should see:

- a `base_url = "..."` line that points to the course proxy
- `env_key = "OPENAI_TOKEN"`
- Your **OpenAI Token** after the second command.
