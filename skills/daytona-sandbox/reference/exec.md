# Executing commands & code, sessions, git

Contents:
- [Run a shell command](#run-a-shell-command)
- [Run code directly (code_run)](#run-code-directly)
- [The stateless trap: cd doesn't persist](#the-stateless-trap)
- [Persistent sessions (multi-step builds)](#persistent-sessions)
- [Environment variables](#environment-variables)
- [Git](#git)

## Run a shell command

```python
resp = sandbox.process.exec("echo hello", cwd="/workspace", env={"X": "1"}, timeout=30)
print(resp.exit_code)   # int
print(resp.result)      # combined stdout
# resp.artifacts.stdout, resp.artifacts.charts (matplotlib chart metadata, if any)
```
`process.exec(command, cwd=None, env=None, timeout=None) -> ExecuteResponse`.
Always check `exit_code` before treating output as success.

## Run code directly

Run a code string in the sandbox's language runtime and capture rich artifacts (e.g.
matplotlib charts) — no shell quoting needed.

```python
from daytona import CodeRunParams
resp = sandbox.process.code_run(
    "import numpy as np; print(np.__version__)",
    params=CodeRunParams(argv=["--flag"], env={"X": "1"}),
    timeout=30,
)
print(resp.result)
charts = resp.artifacts.charts   # chart metadata when the code renders plots
```
`process.code_run(code, params=None, timeout=None) -> ExecuteResponse`.
**There is no MCP equivalent** — `code_run` is SDK-only. Use it instead of hand-quoting
`python3 -c "..."` through `exec`.

## The stateless trap

`process.exec(...)` runs each command in a **fresh shell**. State that lives in a shell —
the current directory (`cd`), shell variables, `source`d envs — does **not** carry to the next
`exec`. (Files written to disk *do* persist; the sandbox filesystem is durable.)

Two correct patterns:
```python
# 1) Chain everything that depends on cwd/shell state in one command:
sandbox.process.exec("cd /app && pip install -e . && pytest -q")

# 2) Use a persistent session (below) when steps are long or numerous.
```

## Persistent sessions

A session is a long-lived shell where state persists across commands — the right tool for
multi-step builds. (SDK-only; the MCP cannot do this.)

```python
from daytona import SessionExecuteRequest

sandbox.process.create_session("build")
r = sandbox.process.execute_session_command(
    "build",
    SessionExecuteRequest(command="cd /app && make", run_async=False),
)
print(r.cmd_id, r.exit_code, r.output, r.stdout, r.stderr)

logs = sandbox.process.get_session_command_logs("build", r.cmd_id)
sandbox.process.list_sessions()        # list[Session]
sandbox.process.get_session("build")
sandbox.process.delete_session("build")
```
`SessionExecuteRequest(command, run_async, suppress_input_echo)`. Use `run_async=True` for
long-running processes (e.g. starting a dev server) and poll logs.

## Environment variables

- Set once for the whole sandbox at create time: `env_vars={"KEY": "value"}`.
- Set per-command: `process.exec(cmd, env={"KEY": "value"})`.
- Keep secrets minimal; only pass what a task needs. Never bake the `DAYTONA_API_KEY` into the
  sandbox.

## Git

Full workflow is SDK-only (the MCP only has `git_clone`):

```python
sandbox.git.clone("https://github.com/org/repo.git", "/workspace/repo",
                  branch="main", commit_id=None, username=None, password=None)
sandbox.git.add("/workspace/repo", ["file.py"])
sandbox.git.commit("/workspace/repo", "msg", author="Me", email="me@x.com")
sandbox.git.push("/workspace/repo", username=None, password=None)
sandbox.git.pull("/workspace/repo")
sandbox.git.status("/workspace/repo")             # GitStatus
sandbox.git.branches("/workspace/repo")
sandbox.git.create_branch("/workspace/repo", "feat")
sandbox.git.checkout_branch("/workspace/repo", "feat")
sandbox.git.delete_branch("/workspace/repo", "feat")
```
For private repos pass `username`/`password` (a token), or clone over an authenticated URL.
