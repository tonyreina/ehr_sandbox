# OpenAI Codex

This setup is for course users using the course OpenAI proxy.

If this is your first time using a terminal, follow the steps exactly as written.

## Quick setup (macOS)

1. Press **Cmd + Space**, type **Terminal**, and press **Enter**.
2. Go to the project folder (adjust the path if you cloned it somewhere else):

```bash
cd ~/ehr_sandbox
```

3. Copy and paste this command, then press **Enter**:

```bash
pixi run codex-setup <openai-token>
```

4. Replace `<openai-token>` with your real **OpenAI Token**.

Or run this instead and paste your **OpenAI Token** when prompted (the input is hidden on purpose):

```bash
pixi run codex-setup
```

On macOS the setup also:

- Saves Codex settings to `~/.codex/config.toml`.
- Adds a line to your shell startup file (`~/.zshrc`, or `~/.bash_profile` if you use bash) that sets `OPENAI_TOKEN` in every new Terminal window.
- Registers `OPENAI_TOKEN` with macOS so VS Code opened from the Dock or Spotlight can see it.

## Quick setup (Windows)

1. Open the **Start menu**.
2. Type **PowerShell**.
3. Click **Windows PowerShell**.
4. In the blue/black window, copy and paste this command, then press **Enter**:

```powershell
pixi run codex-setup <openai-token>
```

5. Replace `<openai-token>` with your real **OpenAI Token**.

Example:

```powershell
pixi run codex-setup gl-abc123efgh4567IJKLM890...
```

If you do not want to paste your **OpenAI Token** in the command, run this instead:

```powershell
pixi run codex-setup
```

Then paste your **OpenAI Token** when prompted (the input is hidden on purpose).

## What this command does automatically

You do **not** need to configure anything manually.

- Saves Codex settings to `%USERPROFILE%\.codex\config.toml`.
- Sets the API base URL to the course proxy endpoint automatically.
- Saves your **OpenAI Token** as a Windows user environment variable named `OPENAI_TOKEN`.

## Finish setup

1. Fully close VS Code (on macOS press **Cmd + Q**; closing the window is not enough).
2. Open VS Code again.
3. Open the Codex extension.

## Simple check (Windows)

Open a **new** PowerShell window and run:

```powershell
Get-Content ~\.codex\config.toml
$env:OPENAI_TOKEN
```

You should see:

- a `base_url = "..."` line that points to the course proxy
- `env_key = "OPENAI_TOKEN"`
- Your **OpenAI Token** printed after the second command.

If you do not see your **OpenAI Token**, close PowerShell and VS Code completely, reopen both, and run the check again.

## Simple check (macOS)

Open a **new** Terminal window and run:

```bash
cat ~/.codex/config.toml
echo $OPENAI_TOKEN
```

You should see the same three things as on Windows: a `base_url` pointing to the course proxy, `env_key = "OPENAI_TOKEN"`, and your **OpenAI Token**.

If the Codex extension still asks for a key, quit VS Code with **Cmd + Q**, then open a new Terminal window and start it from there:

```bash
code
```

The macOS registration lasts until you restart your Mac. After a restart, either start VS Code with `code` from Terminal or run `pixi run codex-setup` again.

## If you use WSL

Run setup in the same place where Codex runs:

- VS Code window says **WSL: Ubuntu** -> run setup in the WSL terminal.
- Normal VS Code window (not WSL) -> run setup in Windows PowerShell.

If you use both, run setup in both.

The setup script is in `ehr/codex.py`.
