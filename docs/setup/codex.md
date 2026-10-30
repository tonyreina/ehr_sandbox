# Connect Codex

Save your course token so Codex and the dashboard's **Ask AI** tab can use it. Run everything in the VS Code terminal (**Terminal > New Terminal**). The commands are the same on Windows, macOS, Ubuntu and WSL.

## 1. Save your token

```bash
pixi run codex-setup <your-token>
```

For example: `pixi run codex-setup gh-abcd1234EFGH5678ijk90`. Leave the token off and you are asked for it (what you type is hidden).

## 2. Restart VS Code

Close it completely (on macOS press **Cmd + Q**) and open it again.

## 3. Check it works

```bash
pixi run codex-check
```

You should see something like this:

```text
Proxy:  https://aibe.mygreatlearning.com/openai/v1
Model:  gpt-5.3-codex
Token:  gl-U2F...WQWh (67 characters, from the environment)
Result: OK - the model answered: Metformin 500 mg (**Medications**).
```

`Result: OK` means your token works. Next: [Start the practice patients](local-hapi.md).

## If something goes wrong

| Problem | Fix |
|---|---|
| `Result: FAILED` and `token invalid` | The token is wrong or expired. Get your current token from the course, run `codex-setup` again, then re-run the check. For any other reason, send the line to your instructor. |
| The Codex extension still asks for a key | Quit VS Code and start it from a terminal with `code`. On macOS you need this after restarting your Mac. |
| You use WSL | Run `codex-setup` in the terminal of the window you use: a window that says **WSL: Ubuntu** at the bottom left, or a normal Windows one. If you use both, run it in both. |

`codex-setup` saves a Codex config in your home folder (`~/.codex/config.toml`) and your token in an `OPENAI_TOKEN` environment variable. The code is in `ehr/codex.py`. Add `--raw` to `codex-check` to see the proxy's full reply.
