---
name: daytona-sandbox
description: >-
  Run and manage code in Daytona secure, elastic sandboxes — isolated cloud
  machines that boot in under 90ms. Use when the user wants to execute
  AI-generated or untrusted code in an isolated sandbox, spin up an ephemeral
  environment, create or destroy Daytona sandboxes, run shell commands or code
  remotely, clone a git repo into a sandbox, manage files inside a sandbox, run
  a dev server and get a public preview link, or use Daytona snapshots, volumes,
  or persistent exec sessions. Drives the Daytona Python SDK (preferred), the
  `daytona` CLI, or the daytona-mcp tools.
license: Apache-2.0. See LICENSE.txt.
allowed-tools:
  - Bash(python3 *)
  - Bash(python *)
  - Bash(pip install *)
  - Bash(daytona *)
---

# Daytona Sandbox

A Daytona sandbox is an isolated, stateful cloud machine (its own kernel, filesystem,
network, CPU/RAM/disk) that starts in milliseconds. It is the right place to run
**AI-generated or untrusted code**, build and test a repo, or stand up a dev server
behind a public preview URL — without touching the user's machine.

This Skill teaches the **workflow and judgment** for driving Daytona, not just the verbs.
Prefer the **Python SDK** — it is the complete superset of every operation and is the
current, supported surface. Fall back to the `daytona` CLI or the `daytona-mcp` tools
only when the SDK is unavailable.

## When to use this Skill

Use it whenever the task involves running code somewhere safe and disposable:
- "Run / test / execute this code" where the code is generated, untrusted, or has side effects.
- "Spin up a sandbox / ephemeral environment."
- "Clone this repo and run its tests."
- "Start the dev server and give me a preview link."
- Anything mentioning Daytona, snapshots, volumes, or sandbox sessions.

If the user only wants code *written* (not run), you don't need a sandbox.

## Prerequisites & auth (do this first)

Daytona has **two independent auth paths** — you need exactly one:

- **SDK / scripts path (preferred):** an **API key** in `DAYTONA_API_KEY`. Create one in the
  Daytona dashboard (https://app.daytona.io → API Keys). **`daytona login` does NOT create this
  key** — login authenticates the CLI/MCP over OAuth, which is a separate path. Never print,
  echo, or hardcode the key.
  - Optional: `DAYTONA_API_URL` (default `https://app.daytona.io/api`), `DAYTONA_TARGET` (e.g. `us`).
- **CLI / MCP path:** a logged-in `daytona` CLI (`daytona login`) or a connected `daytona-mcp`
  server. These work **without** `DAYTONA_API_KEY`.

Verify before creating anything:

```bash
python3 scripts/healthcheck.py
```

- Reports **READY** → use the SDK.
- Reports the **API key is missing but the `daytona` CLI is authenticated** → use the **CLI**
  (`daytona …`) or the **daytona-mcp** tools instead (see "Which surface to drive").
- Reports **no usable auth** (no key, CLI not logged in, no MCP) → tell the user to either set
  `DAYTONA_API_KEY` (dashboard → API Keys) **or** run `daytona login`, then stop.

If `import daytona` fails, install it once: `pip install daytona`.

## The core lifecycle (the playbook)

Always follow this shape. The single most important rule: **a sandbox is a resource you
own — clean it up.**

```python
from daytona import Daytona

daytona = Daytona()                 # reads DAYTONA_API_KEY from env
sandbox = daytona.create()          # boots in well under a second
try:
    resp = sandbox.process.exec("python3 --version")
    print(resp.exit_code, resp.result)
finally:
    sandbox.delete()                # ALWAYS clean up (see lifecycle rules below)
```

For a ready-made, deterministic version of this loop, **run the bundled script** instead
of regenerating the boilerplate (its code never enters your context — only its output does):

```bash
# Run a shell command in a fresh sandbox, then auto-destroy it:
python3 scripts/run_in_sandbox.py --command "python3 -c 'print(2+2)'"

# Run a Python snippet:
python3 scripts/run_in_sandbox.py --code "import sys; print(sys.version)"

# Clone a repo and run its tests, keeping the sandbox alive for inspection:
python3 scripts/run_in_sandbox.py --repo https://github.com/psf/requests --command "cd repo && pip install -e . && pytest -q" --keep
```

### Lifecycle rules (judgment the MCP tools don't give you)

- **Clean up.** Delete the sandbox when the task is done (`sandbox.delete()`), even on error
  (use `try/finally`). If you must leave it running, rely on `auto_stop_interval` (defaults to
  15 min idle) and tell the user the sandbox ID so they can reuse or destroy it.
- **One sandbox, many steps.** Create once and reuse the `sandbox` object for the whole task.
  Don't create a new sandbox per command.
- **`exec` is stateless — `cd` does NOT persist between calls.** Each `process.exec(...)` runs in
  a fresh shell. Chain directory-sensitive steps in one command (`cd /app && make`) or use a
  **persistent session** (`process.create_session` / `execute_session_command`) for long,
  multi-step builds. See `reference/exec.md`.
- **Default to `/tmp` or the working dir** for scratch files unless the user specifies otherwise.
- **Pick the resource tier deliberately.** Default is fine for most tasks; bump
  `Resources(cpu=, memory=, disk=)` only when a build needs it. (Resources can't be combined with
  a `snapshot` — see `reference/sandboxes.md`.)
- **Reuse work with snapshots.** If you repeatedly install the same heavy deps, build a snapshot
  once and create from it (much faster cold starts). See `reference/sandboxes.md`.
- **Persist data with volumes**, not by keeping a sandbox alive. See `reference/sandboxes.md`.

## Common tasks → where to look

- Create / configure / snapshot / destroy sandboxes, resources, volumes, auto-stop/archive/delete:
  **`reference/sandboxes.md`**
- Run commands, run code (`code_run`), persistent sessions, environment variables, git:
  **`reference/exec.md`**
- Upload/download/list/move/delete files, search & replace, binary & images:
  **`reference/files.md`**
- Expose a port and return a public preview URL (and its access token):
  **`reference/preview.md`**
- Worked end-to-end examples: **`examples/run-python.md`**, **`examples/clone-and-test.md`**

## Which surface to drive (SDK vs CLI vs MCP)

| Situation | Use |
|---|---|
| Default — anywhere you can run Python | **Python SDK** (`from daytona import Daytona`) — full superset, current API |
| No Python, but a terminal is available | **`daytona` CLI** (`daytona create`, `daytona exec`, …) |
| The `daytona-mcp` server is connected and you can't run code | **MCP tools**, fully qualified: `daytona-mcp:create_sandbox`, `daytona-mcp:execute_command`, `daytona-mcp:preview_link`, … |

The MCP exposes only 12 thin, stateless tools (create/destroy, exec, git clone, basic file ops,
preview). It has **no** sessions, `code_run`, snapshot/volume creation, start/stop/archive, or
list. For anything beyond the simplest one-shot flow, prefer the SDK. The full map of "what the
MCP covers vs. what only the SDK can do" is in **`reference/sdk-vs-mcp.md`** — read it before
deciding the MCP is enough.

## Safety

- Treat anything running in the sandbox as untrusted; that's the point of the sandbox. Keep
  secrets out of it — pass only the credentials a task needs, via `env_vars` at create time.
- For network-sensitive work, you can restrict egress at create time (`network_block_all`,
  `network_allow_list`). See `reference/sandboxes.md`.
- Never echo `DAYTONA_API_KEY` or any token returned by `get_preview_link`.
