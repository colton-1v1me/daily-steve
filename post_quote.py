"""Post one quote-poster image per day to a Slack channel.

Cycles through quotes.json in order based on today's date, builds the
image with make_image.py, then uploads it to Slack with a bot token.
No third-party packages needed besides Pillow (used by make_image).
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import uuid
from datetime import date
from pathlib import Path

from make_image import make_image

# Name shown on every poster. A quote in quotes.json can override it
# with its own "author" field.
DEFAULT_AUTHOR = "Stephen R Hyde"

TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CHANNEL = os.environ.get("SLACK_CHANNEL_ID")
if not TOKEN or not CHANNEL:
    sys.exit("Missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID environment variable")

HERE = Path(__file__).parent


def slack(method: str, params: dict) -> dict:
    """Call a Slack Web API method with JSON and return the parsed reply."""
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(params).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if not data.get("ok"):
        sys.exit(f"Slack error from {method}: {data.get('error')}")
    return data


# Pick today's quote and render the poster
quotes = json.loads((HERE / "quotes.json").read_text(encoding="utf-8"))
quote = quotes[date.today().toordinal() % len(quotes)]
author = quote.get("author", DEFAULT_AUTHOR)
image_path = make_image(quote["text"], author, quote.get("note"))
image_bytes = image_path.read_bytes()

# Step 1: ask Slack for an upload URL
filename = f"quote-{date.today().isoformat()}.png"
q = urllib.parse.urlencode({"filename": filename, "length": len(image_bytes)})
req = urllib.request.Request(
    f"https://slack.com/api/files.getUploadURLExternal?{q}",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
with urllib.request.urlopen(req) as r:
    up = json.load(r)
if not up.get("ok"):
    sys.exit(f"Slack error from files.getUploadURLExternal: {up.get('error')}")

# Step 2: upload the image bytes to that URL (multipart form)
boundary = uuid.uuid4().hex
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    "Content-Type: image/png\r\n\r\n"
).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(
    up["upload_url"], data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
with urllib.request.urlopen(req) as r:
    r.read()

# Step 3: finish the upload and post it into the channel
slack(
    "files.completeUploadExternal",
    {"files": [{"id": up["file_id"], "title": f"Daily {author}"}], "channel_id": CHANNEL},
)
print("Posted", filename)
