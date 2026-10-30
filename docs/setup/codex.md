# OpenAI Codex

The course uses OpenAI Codex through the Great Learning proxy. One command points Codex at the proxy and stores your learner key so every future session picks it up.

```bash
pixi run codex-setup <learner-api-key>
```

Omit the key to be prompted for it (input is hidden).

## What it does

- Writes `~/.codex/config.toml` (`%USERPROFILE%\.codex\config.toml` on Windows) with the proxy URL, model and `env_key = "CODEX_LEARNER_KEY"`. An existing config that this script did not write is saved to `config.toml.bak`.
- Stores the key for future sessions. On macOS, Linux and WSL it adds `export CODEX_LEARNER_KEY=...` to your shell rc file (`~/.zshrc`, `~/.bashrc` or `~/.profile`); macOS also runs `launchctl setenv` so apps launched from the Dock see the key. On Windows it sets a user environment variable with `setx`.
- Is safe to re-run, for example to rotate your key.

The key lives only in your home directory, never in this repository.

## After running it

1. Fully quit VS Code (Cmd+Q on macOS), then reopen it. Or open a new terminal and run `code`.
2. Open the Codex extension. It connects without asking for a key.

To verify (open a new terminal first):

```bash
cat ~/.codex/config.toml
echo $CODEX_LEARNER_KEY
```

```powershell
Get-Content ~\.codex\config.toml
$env:CODEX_LEARNER_KEY
```

## Windows with WSL

Run the command in the environment where the Codex extension runs. A VS Code window connected to WSL ("WSL: Ubuntu" in the corner) uses the Linux side, so run it in the WSL terminal. A normal Windows window uses Windows, so run it in PowerShell. If you use both, run it in both.

The code is [ehr/codex.py](https://github.com/tonyreina/ehr_sandbox/blob/main/ehr/codex.py). Edit the proxy URL, model and reasoning effort at the top of that file.
