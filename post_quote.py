"""Post one quote per day to a Slack channel via an Incoming Webhook.

Cycles through quotes.json in order based on today's date, so every quote
gets posted once before any repeat. No third-party packages needed.
"""
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

# Name shown under each quote. A quote in quotes.json can override it
# with its own "author" field.
DEFAULT_AUTHOR = "Stephen R Hyde"

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
if not WEBHOOK_URL:
    sys.exit("Missing SLACK_WEBHOOK_URL environment variable")


def escape(text: str) -> str:
    # Slack requires these three characters to be escaped in message text
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


quotes = json.loads((Path(__file__).parent / "quotes.json").read_text(encoding="utf-8"))
quote = quotes[date.today().toordinal() % len(quotes)]

text = escape(quote["text"])
author = escape(quote.get("author", DEFAULT_AUTHOR))
note = quote.get("note")

lines = [f">“{text}”"]
if note:
    lines.append(f">_[{escape(note)}]_")
lines.append(f">— *{author}*")

payload = {
    "text": f"“{text}” — {author}",  # plain-text fallback for notifications
    "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}}],
}

req = urllib.request.Request(
    WEBHOOK_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    print(resp.status, resp.read().decode())
