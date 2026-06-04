# Example: clone a repo, install, run tests, return a preview

Goal: clone a project, run its test suite, and (optionally) start its dev server with a public
preview link — all in one disposable sandbox.

```python
from daytona import Daytona, SessionExecuteRequest

daytona = Daytona()
sandbox = daytona.create()
try:
    # 1. Clone
    sandbox.git.clone("https://github.com/org/repo.git", "/workspace/repo", branch="main")

    # 2. Install + test. Chain cwd-sensitive steps in ONE command (exec is stateless).
    resp = sandbox.process.exec("cd /workspace/repo && pip install -e . && pytest -q", timeout=600)
    print(resp.exit_code, resp.result)
    if resp.exit_code != 0:
        raise SystemExit("tests failed")

    # 3. (optional) Start a dev server in a background session and expose it.
    sandbox.process.create_session("web")
    sandbox.process.execute_session_command(
        "web",
        SessionExecuteRequest(command="cd /workspace/repo && nohup python3 -m http.server 8000 &",
                              run_async=True),
    )
    print("preview:", sandbox.get_preview_link(8000).url)
finally:
    # Keep the sandbox if the user wants to interact with the preview; otherwise delete.
    sandbox.delete()
```

CLI/MCP shortcut for the simple case (clone + one command, no session):

```bash
python3 scripts/run_in_sandbox.py \
  --repo https://github.com/org/repo \
  --command "cd repo && pip install -e . && pytest -q" --keep
```

Tips:
- Bump resources for heavy builds: `Resources(cpu=4, memory=8)` at create time.
- If you keep the sandbox alive for the preview, tell the user its ID and that it will auto-stop
  after `auto_stop_interval` minutes.
