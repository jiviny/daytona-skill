#!/usr/bin/env python3
"""Verify the environment is ready to use Daytona, without creating any sandbox.

Checks, in order:
  1. DAYTONA_API_KEY is present in the environment.
  2. The `daytona` Python SDK is importable (hint to `pip install daytona` if not).
  3. The control plane is reachable and the key is valid (a cheap list call).

Exits 0 if ready, non-zero otherwise. Never prints the API key.
Run:  python3 scripts/healthcheck.py
"""
import os
import sys


def main() -> int:
    key = os.environ.get("DAYTONA_API_KEY")
    if not key:
        print("NOT READY: DAYTONA_API_KEY is not set.")
        print("  Fix: get a key at https://app.daytona.io and export DAYTONA_API_KEY,")
        print("       or run `daytona login`. Then re-run this check.")
        return 2
    print("OK: DAYTONA_API_KEY is set (%d chars)." % len(key))

    api_url = os.environ.get("DAYTONA_API_URL", "https://app.daytona.io/api")
    target = os.environ.get("DAYTONA_TARGET")
    print("    DAYTONA_API_URL=%s  DAYTONA_TARGET=%s" % (api_url, target or "(default)"))

    try:
        from daytona import Daytona  # noqa: F401
    except Exception as exc:  # ImportError or transitive failure
        print("NOT READY: cannot import the daytona SDK (%s)." % exc)
        print("  Fix: pip install daytona")
        return 3
    print("OK: daytona SDK importable.")

    # Cheap authenticated round-trip to confirm connectivity + credentials.
    try:
        from daytona import Daytona
        client = Daytona()
        sandboxes = list(client.list())
        print("OK: reached Daytona control plane (%d sandbox(es) visible)." % len(sandboxes))
    except Exception as exc:
        print("NOT READY: could not reach Daytona or the key was rejected (%s)." % exc)
        print("  Fix: confirm the key is valid and DAYTONA_API_URL is correct.")
        return 4

    print("READY: you can create and drive Daytona sandboxes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
