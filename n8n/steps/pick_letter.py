"""Pick the letter and the token counts out of the AI's reply.

The n8n workflow sends the AI's reply to run(). What run() returns goes back to the workflow.
Edit this file in VS Code and save it: the next draft uses your change. No restart, no publishing.
"""


def run(reply: dict) -> dict:
    # The reply holds a list of messages; the letter is the text parts of the message.
    letter = "".join(
        part.get("text", "")
        for item in reply.get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    ).strip()

    usage = reply.get("usage") or {}
    return {
        "letter": letter,
        "model": reply.get("model"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cached_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens", 0),
    }
