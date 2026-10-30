# OpenAI Codex

This setup is for course users using the course OpenAI proxy. All lessons use **VS Code**, so every step below happens inside VS Code.

If this is your first time using a terminal, follow the steps exactly as written.

## Quick setup

1. Open the `ehr_sandbox` project folder in VS Code (**File > Open Folder**).
2. Open the terminal in VS Code: **Terminal > New Terminal**. It opens at the bottom of the window, already in the project folder, so you do not need to `cd` anywhere.
3. Copy and paste this command into the terminal, then press **Enter**:

    ```bash
    pixi run codex-setup <openai-token>
    ```

4. Replace `<openai-token>` with your real **OpenAI Token**.

    Example:

    ```bash
    pixi run codex-setup gh-abcd1234EFGH5678ijk90
    ```

Or run this instead and paste your **OpenAI Token** when prompted (the input is hidden on purpose):

```bash
pixi run codex-setup
```

The same command works on Windows, macOS, Ubuntu and WSL.

## What this command does automatically

You do **not** need to configure anything manually.

- Saves Codex settings to `config.toml` in the `.codex` folder in your home directory.
- Sets the API base URL to the course proxy endpoint automatically.
- Saves your **OpenAI Token** in an environment variable named `OPENAI_TOKEN`:
    - **Windows:** a user environment variable.
    - **macOS:** a line in `~/.zshrc` (or `~/.bash_profile` if you use bash), plus a registration with macOS so VS Code opened from the Dock or Spotlight can see it.
    - **Ubuntu and WSL:** a line in `~/.bashrc` (or `~/.zshrc` if you use zsh).

## Finish setup

VS Code only reads the token when it starts, so you must restart it completely:

1. Fully close VS Code (on macOS press **Cmd + Q**; closing the window is not enough).
2. Open VS Code again.
3. Open the Codex extension.

## Simple check

Open a **new** terminal in VS Code (**Terminal > New Terminal**) and run:

=== "Windows (PowerShell)"

    ```powershell
    Get-Content ~\.codex\config.toml
    $env:OPENAI_TOKEN
    ```

=== "macOS / Ubuntu / WSL"

    ```bash
    cat ~/.codex/config.toml
    echo $OPENAI_TOKEN
    ```

You should see:

- a `base_url = "..."` line that points to the course proxy
- `env_key = "OPENAI_TOKEN"`
- Your **OpenAI Token** printed after the second command.

If you do not see your **OpenAI Token**, fully close VS Code, reopen it, and run the check again.

## Check the connection

After setup, test your token against the course proxy. Run this in the VS Code terminal:

```bash
pixi run codex-check
```

It prints the proxy address, the model, a masked copy of your token and where it was found, then sends one tiny test question. You should see something like this:

```text
Proxy:  https://aibe.mygreatlearning.com/openai/v1
Model:  gpt-5.3-codex
Token:  gl-U2F...WQWh (67 characters, from the environment)
Result: OK - the model answered: Metformin 500 mg (**Medications**).
```

`Result: OK` means your token works and the dashboard's Ask box will work. The token line shows only the first and last few characters; the character count and the wording of the answer will differ for you.

If you see `Result: FAILED`, the message includes the reason the proxy gave. For example, `Authentication failed: token invalid` means the token is wrong or has expired: get your current token from the course, run `pixi run codex-setup <openai-token>` again, and re-run the check. For any other reason, send the line to your instructor.

## If the Codex extension still asks for a key

On macOS the registration with the Dock lasts only until you restart your Mac, and on Ubuntu a VS Code started from the app launcher does not read `~/.bashrc`. In both cases, fully quit VS Code and start it from a terminal instead:

```bash
code
```

Or run `pixi run codex-setup` again.

## If you use WSL

Run setup in the same place where Codex runs:

- VS Code window says **WSL: Ubuntu** in the bottom-left corner -> run setup in that window's terminal.
- Normal VS Code window (not WSL) -> run setup in that window's terminal (PowerShell on Windows).

If you use both, run setup in both.

The setup script is in `ehr/codex.py`.
