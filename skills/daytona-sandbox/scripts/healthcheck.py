#!/usr/bin/env python3
"""Verify the environment is ready to use Daytona, without creating any sandbox.

Daytona has two independent auth paths:
  * SDK / scripts path  -> needs an API key in DAYTONA_API_KEY (dashboard -> API Keys).
  * CLI / MCP path       -> a logged-in `daytona` CLI or a connected daytona-mcp server,
                            which work WITHOUT DAYTONA_API_KEY.

This check reports which path is usable. Exit 0 = at least one path is ready.
Never prints the API key. Run:  python3 scripts/healthcheck.py
"""
import os
import shutil
import subprocess
import sys


def cli_authenticated():
    """Return True/False if the `daytona` CLI is installed and logged in, or None if absent."""
    exe = shutil.which("daytona")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "sandbox", "list"], capture_output=True, text=True, timeout=25)
        return r.returncode == 0
    except Exception:
        return False


def main() -> int:
    key = os.environ.get("DAYTONA_API_KEY")

    if not key:
        # No SDK key — see whether the CLI/MCP path is available instead.
        auth = cli_authenticated()
        if auth is True:
            print("PARTIAL: DAYTONA_API_KEY is not set, but the `daytona` CLI is authenticated.")
            print("  -> Use the CLI (`daytona ...`) or the daytona-mcp tools.")
            print("  -> The Python SDK and scripts/run_in_sandbox.py need an API key; set")
            print("     DAYTONA_API_KEY (dashboard -> API Keys) to use them.")
            return 0
        if auth is False:
            print("NOT READY: DAYTONA_API_KEY is not set and the `daytona` CLI is not")
            print("  authenticated (your login may have expired).")
            print("  Fix: run `daytona login`, or set DAYTONA_API_KEY (dashboard -> API Keys).")
            return 2
        print("NOT READY: DAYTONA_API_KEY is not set and the `daytona` CLI was not found.")
        print("  Fix: set DAYTONA_API_KEY (https://app.daytona.io -> API Keys),")
        print("       or install the CLI and run `daytona login`.")
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

    print("READY: you can create and drive Daytona sandboxes via the SDK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
