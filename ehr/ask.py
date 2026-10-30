"""Ask a question about a patient chart through the course's OpenAI proxy.

The token (OPENAI_TOKEN, saved by `pixi run codex-setup`) is read here, on the server side,
and never sent to the browser. The chart text is sent to the model together with the question.
"""
import os

import requests

from ehr import codex

INSTRUCTIONS = """You are a clinical assistant helping a healthcare professional read a patient chart.
The chart is synthetic teaching data.

Rules:
- Answer only from the chart text provided. Do not use outside knowledge about this patient.
- If the chart does not contain the answer, say "Not documented in this chart." Never guess.
- Name the chart section each fact comes from (for example "Medications" or "Results").
- If sections disagree, or something looks unsafe or missing, say so plainly.
- Keep answers short and in plain language. You support a clinician's judgment; you do not replace it.
"""

MAX_CHART = 60_000
MAX_QUESTION = 2_000


class AskError(Exception):
    """A problem to show the learner (never contains the token)."""


def token() -> str | None:
    return (os.getenv(codex.ENV_VAR) or "").strip() or None


def _output_text(data: dict) -> str:
    """The model's text from a Responses API reply."""
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    parts = [c.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
             for c in item.get("content", []) if c.get("type") == "output_text"]
    return "".join(parts)


def ask(chart: str, question: str, base_url: str = codex.PROXY_URL) -> str:
    key = token()
    if not key:
        raise AskError(f"No {codex.ENV_VAR} found. Run `pixi run codex-setup`, then fully restart VS Code "
                       "and start the dashboard again.")
    question = question.strip()
    if not question:
        raise AskError("Type a question first.")
    if len(question) > MAX_QUESTION:
        raise AskError(f"Question is too long (limit {MAX_QUESTION} characters).")
    if len(chart) > MAX_CHART:
        chart = chart[:MAX_CHART] + "\n[chart truncated]"
    body = {"model": codex.DEFAULT_MODEL, "instructions": INSTRUCTIONS,
            "input": f"CHART:\n{chart}\n\nQUESTION: {question}"}
    try:
        r = requests.post(f"{base_url.rstrip('/')}/responses", json=body, timeout=120,
                          headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise AskError(f"Could not reach the course proxy ({type(e).__name__}). Check your connection.")
    if r.status_code in (401, 403):
        raise AskError("The course proxy rejected your token. Check it, then run `pixi run codex-setup` again.")
    if not r.ok:
        raise AskError(f"The course proxy returned an error ({r.status_code}).")
    try:
        text = _output_text(r.json()).strip()
    except ValueError:
        text = ""
    if not text:
        raise AskError("The model returned no answer. Try rephrasing the question.")
    return text
