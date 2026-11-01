"""Run n8n (visual workflows) in Docker, next to the local HAPI server.

n8n joins the same Docker network as HAPI, so a workflow reads patients from http://ehr-hapi:8080/fhir.
The course token is passed in as an environment variable (never written to the workflow files), so a
workflow can call the course proxy with {{ $env.OPENAI_TOKEN }}. The starter workflows in n8n/workflows
are imported the first time n8n starts; later starts keep whatever the learner changed.
"""
import json
import os
import subprocess
import time
from pathlib import Path

import requests

from ehr import ask, codex, hapi_local

CONTAINER = "ehr-n8n"
VOLUME = "ehr-n8n-data"
IMAGE = "docker.n8n.io/n8nio/n8n:2.45.7"
PORT = 5678
URL = f"http://localhost:{PORT}"
WORKFLOWS = Path(__file__).parent.parent / "n8n" / "workflows"
STARTER_WEBHOOKS = ("referral",)                    # webhook paths of the starter workflows
IMPORTED = "/home/node/.n8n/.ehr-imported"          # marker in the data volume: starter workflows are in


def _docker(*args: str, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, text=True, capture_output=True, env=env)


def _exists() -> bool:
    return CONTAINER in _docker("ps", "-a", "--format", "{{.Names}}").stdout.split()


def ready() -> bool:
    """True once n8n has finished its own database setup (/healthz answers a few seconds earlier)."""
    try:
        return requests.get(f"{URL}/healthz/readiness", timeout=3).ok
    except requests.RequestException:
        return False


def _exec(*args: str, tries: int = 6, delay: int = 5) -> None:
    """docker exec in the n8n container, retrying: right after a first start n8n can still be busy with
    its database. The error shown is n8n's own message, not just an exit code."""
    last = ""
    for attempt in range(tries):
        r = _docker("exec", CONTAINER, *args, check=False)
        if r.returncode == 0:
            return
        last = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["no message"]
        last = last[0][:300]
        if attempt < tries - 1:
            time.sleep(delay)
    raise RuntimeError(f"`n8n {' '.join(args[1:3])}` failed: {last}")


def _wait(timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ready():
            return
        time.sleep(2)
    raise RuntimeError(f"n8n did not answer within {timeout}s; see `docker logs {CONTAINER}`")


def _wait_webhooks(timeout: int) -> None:
    """Wait until the published workflows are listening. n8n answers /healthz a little before that.

    A GET to a POST-only webhook gets "not registered for GET" once it is live, and plain "not registered" before.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{URL}/webhook/{STARTER_WEBHOOKS[0]}", timeout=3)
            if r.status_code == 404 and "POST" in r.text:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError(f"The workflows did not become active within {timeout}s; see `docker logs {CONTAINER}`")


def _run_container(ai_base_url: str) -> None:
    hapi_local.ensure_network()
    _docker("rm", "-f", CONTAINER, check=False)           # recreated each time so a new token is picked up
    # "-e OPENAI_TOKEN" with no value passes it from this process, so it never appears on a command line.
    env = {**os.environ, codex.ENV_VAR: ask.token() or ""}
    _docker(
        "run", "-d", "--name", CONTAINER, "--network", hapi_local.NETWORK,
        "--add-host", "host.docker.internal:host-gateway",
        "-p", f"127.0.0.1:{PORT}:5678",
        "-v", f"{VOLUME}:/home/node/.n8n", "-v", f"{WORKFLOWS}:/workflows:ro",
        "-e", f"HAPI_BASE=http://{hapi_local.CONTAINER}:8080/fhir",
        "-e", f"AI_BASE_URL={ai_base_url}", "-e", f"AI_MODEL={codex.DEFAULT_MODEL}", "-e", codex.ENV_VAR,
        "-e", "N8N_BLOCK_ENV_ACCESS_IN_NODE=false",       # workflows read the settings above with $env
        "-e", "N8N_SECURE_COOKIE=false", "-e", "N8N_DIAGNOSTICS_ENABLED=false",
        "-e", "N8N_PERSONALIZATION_ENABLED=false", "-e", "N8N_VERSION_NOTIFICATIONS_ENABLED=false",
        "-e", "N8N_RUNNERS_ENABLED=true",
        IMAGE, env=env,
    )


def _import_starters() -> None:
    """Import and publish the starter workflows once (a marker in the data volume remembers it)."""
    if _docker("exec", CONTAINER, "test", "-f", IMPORTED, check=False).returncode == 0:
        return
    _exec("n8n", "import:workflow", "--separate", "--input=/workflows")
    for f in sorted(WORKFLOWS.glob("*.json")):
        _exec("n8n", "publish:workflow", f"--id={json.loads(f.read_text(encoding='utf-8'))['id']}")
    _docker("exec", CONTAINER, "touch", IMPORTED)
    _docker("restart", CONTAINER)                         # published workflows are registered on start


def up(timeout: int = 180, ai_base_url: str = codex.PROXY_URL, reset_workflows: bool = False) -> str:
    """Start n8n (HAPI should be running too) and wait until it answers. Returns its address."""
    _run_container(ai_base_url)
    _wait(timeout)
    if reset_workflows:
        _docker("exec", CONTAINER, "rm", "-f", IMPORTED, check=False)
    _import_starters()
    _wait(timeout)
    _wait_webhooks(timeout)
    return URL


def down(delete_data: bool = False) -> None:
    """Stop and remove n8n; its data volume (accounts, edited workflows) stays unless *delete_data*."""
    _docker("rm", "-f", CONTAINER, check=False)
    if delete_data:
        _docker("volume", "rm", "-f", VOLUME, check=False)
