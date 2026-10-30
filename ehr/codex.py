"""Configure OpenAI Codex for the course proxy (Windows, macOS, Linux, WSL)."""
import os
import re
import subprocess
import sys
from pathlib import Path

PROXY_URL = "https://aibe." + "my" + "great" + "learning.com/openai/v1"
PROVIDER_ID = "course_proxy"
PROVIDER_NAME = "Course Proxy"
DEFAULT_MODEL = "gpt-5.3-codex"
REASONING_EFFORT = "medium"         # none | minimal | low | medium | high | xhigh
ENV_VAR = "OPENAI_TOKEN"

MARKER = "Managed by codex-setup"
BLOCK_START = "# >>> codex-token >>>"
BLOCK_END = "# <<< codex-token <<<"
LEGACY_BLOCK_START = "# >>> codex-learner-key >>>"
LEGACY_BLOCK_END = "# <<< codex-learner-key <<<"

CONFIG_TOML = f"""# {MARKER} - do not edit manually
# Schema: https://developers.openai.com/codex/config-schema.json

model = "{DEFAULT_MODEL}"
model_provider = "{PROVIDER_ID}"
model_reasoning_effort = "{REASONING_EFFORT}"

[model_providers.{PROVIDER_ID}]
name = "{PROVIDER_NAME}"
base_url = "{PROXY_URL}"
env_key = "{ENV_VAR}"
wire_api = "responses"
"""


def config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def write_config() -> tuple[Path, Path | None]:
    """Write ~/.codex/config.toml. Returns (path, backup path if one was made)."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if path.exists() and MARKER not in existing and f'env_key = "{ENV_VAR}"' not in existing:
        backup = path.with_name(path.name + ".bak")
        backup.write_bytes(path.read_bytes())
    path.write_text(CONFIG_TOML, encoding="utf-8")
    return path, backup


def rc_file() -> Path:
    """The shell startup file that should export the key (macOS / Linux / WSL)."""
    home = Path.home()
    shell = Path(os.environ.get("SHELL", "/bin/bash")).name
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "bash":
        if sys.platform == "darwin" and (home / ".bash_profile").exists():
            return home / ".bash_profile"
        return home / ".bashrc"
    return home / ".profile"


def _drop_rc_block(text: str, start: str, end: str) -> str:
    return re.sub(rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?", "\n", text, flags=re.S)


def _write_rc_block(rc: Path, key: str) -> None:
    text = rc.read_text(encoding="utf-8") if rc.exists() else ""
    text = _drop_rc_block(text, BLOCK_START, BLOCK_END)
    text = _drop_rc_block(text, LEGACY_BLOCK_START, LEGACY_BLOCK_END)
    quoted = key.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
    text = text.rstrip("\n") + (
        f"\n\n{BLOCK_START}\n# {MARKER} Codex setup - do not edit\n"
        f'export {ENV_VAR}="{quoted}"\n{BLOCK_END}\n'
    )
    rc.write_text(text, encoding="utf-8")


def store_key(key: str) -> str:
    """Persist the key for future sessions. Returns a description of where."""
    if sys.platform == "win32":
        subprocess.run(["setx", ENV_VAR, key], check=True, capture_output=True)
        return "Windows user environment variable"
    rc = rc_file()
    _write_rc_block(rc, key)
    if sys.platform == "darwin":
        subprocess.run(["launchctl", "setenv", ENV_VAR, key], check=False)
    return str(rc)



