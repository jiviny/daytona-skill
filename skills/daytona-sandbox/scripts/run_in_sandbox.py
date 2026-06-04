#!/usr/bin/env python3
"""Create a Daytona sandbox, optionally clone a repo, run a command or code, print the
output, and (by default) destroy the sandbox.

This is the deterministic version of the core lifecycle in SKILL.md. Prefer running it over
re-deriving the boilerplate: the script's code never enters the model's context, only its output.

Examples:
  python3 run_in_sandbox.py --command "python3 -c 'print(2+2)'"
  python3 run_in_sandbox.py --code "import sys; print(sys.version)"
  python3 run_in_sandbox.py --repo https://github.com/psf/requests \\
      --command "cd repo && pip install -e . && pytest -q" --keep
  python3 run_in_sandbox.py --command "python3 -m http.server 8000 &" --preview 8000 --keep

Requires DAYTONA_API_KEY in the environment. Exits with the command's exit code.
"""
import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run a command/code in a fresh Daytona sandbox.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--command", help="Shell command to run (chain cwd-sensitive steps with &&).")
    g.add_argument("--code", help="Code string to run via process.code_run.")
    p.add_argument("--repo", help="Git URL to clone into ./repo before running.")
    p.add_argument("--branch", help="Branch to clone (with --repo).")
    p.add_argument("--image", help="Container image, e.g. 'python:3.12'. Default: SDK default.")
    p.add_argument("--language", default="python", help="Runtime language for --code. Default: python.")
    p.add_argument("--cpu", type=int, help="vCPU cores (cannot combine with a snapshot).")
    p.add_argument("--memory", type=int, help="Memory in GB.")
    p.add_argument("--disk", type=int, help="Disk in GB.")
    p.add_argument("--env", action="append", default=[], metavar="K=V",
                   help="Environment variable for the sandbox (repeatable).")
    p.add_argument("--timeout", type=int, default=300, help="Per-command timeout in seconds.")
    p.add_argument("--preview", type=int, metavar="PORT",
                   help="After running, print a public preview URL for this port (implies --keep).")
    p.add_argument("--keep", action="store_true",
                   help="Do not destroy the sandbox afterward; print its ID for reuse.")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if not args.command and not args.code and not args.repo and args.preview is None:
        print("Nothing to do: pass --command, --code, --repo, or --preview.", file=sys.stderr)
        return 64

    try:
        from daytona import Daytona, CodeRunParams
    except Exception as exc:
        print("Cannot import the daytona SDK (%s). Run: pip install daytona" % exc, file=sys.stderr)
        return 69

    env_vars = {}
    for item in args.env:
        if "=" not in item:
            print("Bad --env %r (expected K=V)" % item, file=sys.stderr)
            return 64
        k, v = item.split("=", 1)
        env_vars[k] = v

    daytona = Daytona()

    # Build create params only if the caller customized the sandbox; otherwise use the default.
    params = None
    if any([args.image, args.cpu, args.memory, args.disk, env_vars]):
        from daytona import CreateSandboxFromImageParams, Resources
        resources = None
        if any([args.cpu, args.memory, args.disk]):
            resources = Resources(cpu=args.cpu, memory=args.memory, disk=args.disk)
        params = CreateSandboxFromImageParams(
            image=args.image or "python:3.12",
            language=args.language,
            resources=resources,
            env_vars=env_vars or None,
            public=args.preview is not None,
        )

    sandbox = daytona.create(params, timeout=max(120, args.timeout))
    keep = args.keep or args.preview is not None
    exit_code = 0
    try:
        print("sandbox: %s" % sandbox.id, file=sys.stderr)

        if args.repo:
            sandbox.git.clone(args.repo, "repo", branch=args.branch)
            print("cloned %s -> repo" % args.repo, file=sys.stderr)

        if args.code:
            resp = sandbox.process.code_run(args.code, params=CodeRunParams(), timeout=args.timeout)
            print(resp.result)
            exit_code = int(getattr(resp, "exit_code", 0) or 0)
        elif args.command:
            resp = sandbox.process.exec(args.command, timeout=args.timeout)
            print(resp.result)
            exit_code = int(getattr(resp, "exit_code", 0) or 0)

        if args.preview is not None:
            link = sandbox.get_preview_link(args.preview)
            print("preview_url: %s" % link.url)
    finally:
        if keep:
            print("kept sandbox %s (will auto-stop per its policy; delete with "
                  "`daytona delete %s`)" % (sandbox.id, sandbox.id), file=sys.stderr)
        else:
            sandbox.delete()
            print("destroyed sandbox %s" % sandbox.id, file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
