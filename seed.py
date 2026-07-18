#!/usr/bin/env python3
"""POST each sample message from SAMPLE_MESSAGES.md to /process."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLE_MESSAGES = ROOT / "SAMPLE_MESSAGES.md"
DEFAULT_BASE_URL = os.environ.get("LRN_BASE_URL", "http://127.0.0.1:8080")


def load_messages(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```(?:\w*)\n(.*?)```", text, flags=re.DOTALL)
    messages: list[str] = []
    for block in blocks:
        message = block.strip()
        if not message or message.startswith("{"):
            continue
        messages.append(message)
    return messages


def post_process(base_url: str, message: str, timeout: float) -> tuple[int, str]:
    url = base_url.rstrip("/") + "/process"
    body = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=SAMPLE_MESSAGES,
        help=f"Markdown file with sample messages (default: {SAMPLE_MESSAGES.name})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=10.0,
        help="Seconds to sleep between messages (default: 10)",
    )
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"Sample messages file not found: {args.file}", file=sys.stderr)
        return 1

    messages = load_messages(args.file)
    if not messages:
        print(f"No sample messages found in {args.file}", file=sys.stderr)
        return 1

    print(f"Seeding {len(messages)} messages via {args.base_url.rstrip('/')}/process")
    failures = 0
    for i, message in enumerate(messages, start=1):
        if i > 1 and args.sleep > 0:
            print(f"  sleeping {args.sleep:g}s...")
            time.sleep(args.sleep)
        preview = message.replace("\n", " ")
        if len(preview) > 72:
            preview = preview[:69] + "..."
        print(f"[{i}/{len(messages)}] {preview}")
        status, body = post_process(args.base_url, message, args.timeout)
        if 200 <= status < 300:
            try:
                summary = json.loads(body).get("summary", "")
            except json.JSONDecodeError:
                summary = body[:120]
            print(f"  -> {status} {summary}")
        else:
            failures += 1
            print(f"  -> {status} {body}", file=sys.stderr)

    if failures:
        print(f"Done with {failures} failure(s).", file=sys.stderr)
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
