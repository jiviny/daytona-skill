# Example: run AI-generated Python safely

Goal: the user asked you to run a piece of Python you (or they) generated, without trusting it
on the local machine.

```python
from daytona import Daytona, CodeRunParams

daytona = Daytona()
sandbox = daytona.create()
try:
    code = r'''
import platform, sys
print("python", sys.version.split()[0], "on", platform.system())
print(sum(range(100)))
'''
    resp = sandbox.process.code_run(code, params=CodeRunParams(), timeout=30)
    print("exit:", resp.exit_code)
    print(resp.result)
finally:
    sandbox.delete()
```

Or, without writing any boilerplate, run the bundled helper (its code never enters context):

```bash
python3 scripts/run_in_sandbox.py --code "print(sum(range(100)))"
```

Notes:
- Use `code_run` (not `exec` with `python3 -c`) so you don't fight shell quoting and you can
  capture chart artifacts.
- For untrusted code that should not reach the network, create with
  `CreateSandboxFromImageParams(image="python:3.12", network_block_all=True)`.
- Always `delete()` in a `finally` block.
