"""Minimal CLI for interacting with a running StudyRAG backend."""
from __future__ import annotations
import argparse
import json
import sys
import urllib.request
import urllib.error

DEFAULT_URL = "http://localhost:8000"


def chat(args) -> None:
    payload = json.dumps({"query": args.query, "agent_type": args.agent}).encode()
    req = urllib.request.Request(
        f"{args.url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        print(f"\n[{data['agent_name']}]\n{data['answer']}\n")
    except urllib.error.URLError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="StudyRAG CLI")
    parser.add_argument("--url", default=DEFAULT_URL)
    sub = parser.add_subparsers(dest="cmd", required=True)
    chat_p = sub.add_parser("chat")
    chat_p.add_argument("query")
    chat_p.add_argument("--agent", default="explainer")
    args = parser.parse_args()
    if args.cmd == "chat":
        chat(args)


if __name__ == "__main__":
    main()
