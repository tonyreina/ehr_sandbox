"""Ask a question about a patient chart through the course's OpenAI proxy.

The token (OPENAI_TOKEN, saved by `pixi run codex-setup`) is read here, on the server side,
and never sent to the browser. The chart text is sent to the model together with the question.
"""
import os
from dataclasses import dataclass, field

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

INPUT_TEMPLATE = "CHART:\n{chart}\n\nQUESTION: {question}"      # the user message; shown in the dashboard

MAX_CHART = 60_000
MAX_QUESTION = 2_000


# USD per million tokens: (input, cached input, output). Third-party price lists for OpenAI's published
# rates (developers.openai.com/api/docs/pricing); the course proxy may bill differently, so costs
# computed from this table are shown as estimates. A cost the proxy reports itself wins.
PRICES = {"gpt-5.3-codex": (1.75, 0.175, 14.00)}


@dataclass
class AskResult:
    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    cost_estimated: bool            # True when computed from PRICES rather than reported by the proxy
    raw: dict = field(default_factory=dict, repr=False)      # the proxy's reply (for `codex-check --raw`)

    def public(self) -> dict:
        """What the dashboard gets: everything except the raw reply."""
        return {k: v for k, v in vars(self).items() if k != "raw"}


class AskError(Exception):
    """A problem to show the learner (never contains the token)."""


def token() -> str | None:
    """OPENAI_TOKEN from the environment, else the copy `codex-setup` saved (no restart needed)."""
    return (os.getenv(codex.ENV_VAR) or "").strip() or codex.saved_token()


def _output_text(data: dict) -> str:
    """The model's text from a Responses API reply."""
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    parts = [c.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
             for c in item.get("content", []) if c.get("type") == "output_text"]
    return "".join(parts)


def _error_detail(r: requests.Response, key: str) -> str:
    """The proxy's own error message, short and with the token removed: ': <message>' or ''."""
    try:
        data = r.json()
        err = data.get("error") or data.get("reason") or data.get("detail") or data.get("message")
        msg = err.get("message") if isinstance(err, dict) else err
    except (ValueError, AttributeError):
        msg = r.text
    msg = " ".join(str(msg or "").split()).replace(key, "[token]")[:200]
    return f": {msg}" if msg else ""


def _price(model: str) -> tuple[float, float, float] | None:
    """Prices for *model*; the longest matching name wins so dated model ids (gpt-5.3-codex-2026-...) work."""
    names = [n for n in PRICES if model.startswith(n)]
    return PRICES[max(names, key=len)] if names else None


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _find_cost(obj, depth: int = 0) -> float | None:
    """A cost anywhere in the reply body: a number under a key containing "cost", or a {total/usd: n} object."""
    if depth > 4:
        return None
    if isinstance(obj, dict):
        for key, value in obj.items():
            if "cost" in key.lower():
                if (n := _number(value)) is not None:
                    return n
                if isinstance(value, dict):
                    for sub in ("total", "total_cost", "usd", "amount"):
                        if (n := _number(value.get(sub))) is not None:
                            return n
        for value in obj.values():
            if (n := _find_cost(value, depth + 1)) is not None:
                return n
    elif isinstance(obj, list):
        for value in obj:
            if (n := _find_cost(value, depth + 1)) is not None:
                return n
    return None


def _reported_cost(headers, body: dict) -> float | None:
    """A cost the proxy states itself: a header with "cost" in its name (for example x-...-response-cost), else the body."""
    for name, value in headers.items():
        if "cost" in name.lower() and (n := _number(value)) is not None:
            return n
    return _find_cost(body)


def ask(chart: str, question: str, base_url: str = codex.PROXY_URL) -> str:
    """Just the answer text."""
    return ask_detail(chart, question, base_url).answer


def ask_detail(chart: str, question: str, base_url: str = codex.PROXY_URL) -> AskResult:
    key = token()
    if not key:
        raise AskError(f"No {codex.ENV_VAR} found. Run `pixi run codex-setup`, then start the dashboard again.")
    question = question.strip()
    if not question:
        raise AskError("Type a question first.")
    if len(question) > MAX_QUESTION:
        raise AskError(f"Question is too long (limit {MAX_QUESTION} characters).")
    if len(chart) > MAX_CHART:
        chart = chart[:MAX_CHART] + "\n[chart truncated]"
    body = {"model": codex.DEFAULT_MODEL, "instructions": INSTRUCTIONS,
            "input": INPUT_TEMPLATE.format(chart=chart, question=question),
            "store": False}        # do not keep the chart and answer on the server
    try:
        r = requests.post(f"{base_url.rstrip('/')}/responses", json=body, timeout=120,
                          headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise AskError(f"Could not reach the course proxy ({type(e).__name__}). Check your connection.")
    if not r.ok:
        detail = _error_detail(r, key)
        if r.status_code in (401, 403):
            raise AskError(f"The course proxy refused the request ({r.status_code}){detail}. Check your token, "
                           "then run `pixi run codex-setup` again, or run `pixi run codex-check`.")
        raise AskError(f"The course proxy returned an error ({r.status_code}){detail}.")
    try:
        data = r.json()
        text = _output_text(data).strip()
    except ValueError:
        data, text = {}, ""
    if not text:
        raise AskError("The model returned no answer. Try rephrasing the question.")
    usage = data.get("usage") or {}
    tokens_in = usage.get("input_tokens", usage.get("prompt_tokens"))
    tokens_out = usage.get("output_tokens", usage.get("completion_tokens"))
    model = data.get("model") or codex.DEFAULT_MODEL
    cost, estimated = _reported_cost(r.headers, data), False
    if cost is None and isinstance(tokens_in, int) and isinstance(tokens_out, int) and (price := _price(model)):
        cached = min((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0, tokens_in)
        cost = ((tokens_in - cached) * price[0] + cached * price[1] + tokens_out * price[2]) / 1_000_000
        estimated = True
    return AskResult(text, model, tokens_in, tokens_out, cost, estimated,
                     raw={"headers": sorted(r.headers), "body": data})
