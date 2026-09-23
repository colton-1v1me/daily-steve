"""Post one quote per day to a Slack channel via an Incoming Webhook.

Picks a quote based on today's date, so it cycles through the whole list
before repeating. No third-party packages needed.
"""
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
if not WEBHOOK_URL:
    sys.exit("Missing SLACK_WEBHOOK_URL environment variable")


def escape(text: str) -> str:
    # Slack requires these three characters to be escaped in message text
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


quotes = json.loads((Path(__file__).parent / "quotes.json").read_text(encoding="utf-8"))
quote = quotes[date.today().toordinal() % len(quotes)]

text = escape(quote["text"])
author = escape(quote["author"])

payload = {
    # Plain-text fallback used in notifications
    "text": f"{text} — {author}",
    "blocks": [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f">_{text}_\n>— *{author}*"},
        }
    ],
}

req = urllib.request.Request(
    WEBHOOK_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    print(resp.status, resp.read().decode())
