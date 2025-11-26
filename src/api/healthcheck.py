"""Standalone healthcheck script (used by Docker HEALTHCHECK)."""
import sys
import urllib.request

URL = "http://localhost:8000/api/health"

try:
    with urllib.request.urlopen(URL, timeout=5) as resp:
        if resp.status == 200:
            sys.exit(0)
        sys.exit(1)
except Exception:
    sys.exit(1)
