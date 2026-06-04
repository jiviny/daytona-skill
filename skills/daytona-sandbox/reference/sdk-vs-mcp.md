# SDK vs MCP: what each surface covers (read before relying on the MCP)

This Skill deliberately does **not** re-document the 12 MCP tools as if they were new
capabilities — they're already a thin layer over the same Daytona REST API the SDK uses. This
page is the honest map so you can pick the right surface and never duplicate effort.

## What the daytona-mcp server is

A **local stdio** MCP server bundled inside the `daytona` CLI binary (run via `daytona mcp start`;
configured with `daytona mcp init claude|cursor|windsurf`). It exposes **exactly 12 tools**, each a
**stateless** wrapper that re-authenticates per call and (for file/exec/git) calls Daytona's
`*Deprecated` toolbox endpoints. Every tool except `create_sandbox` requires the sandbox `id`.

## The 12 MCP tools and their SDK equivalents

| MCP tool | SDK equivalent | Notes |
|---|---|---|
| `create_sandbox` | `daytona.create(...)` | MCP caps cpu≤4, gpu≤1, mem≤8GB, disk≤10GB; SDK does not |
| `destroy_sandbox` | `sandbox.delete()` | — |
| `execute_command` | `sandbox.process.exec()` | MCP is one-shot/stateless; wraps `&&`/`cd` in `/bin/sh -c` |
| `git_clone` | `sandbox.git.clone()` | MCP has clone only; SDK has full git |
| `create_folder` | `sandbox.fs.create_folder(path, mode)` | — |
| `list_files` | `sandbox.fs.list_files()` | — |
| `file_upload` | `sandbox.fs.upload_file()` | MCP requires `encoding`+`overwrite` even for trivial text |
| `file_download` | `sandbox.fs.download_file()` | MCP special-cases images & matplotlib JSON |
| `move_file` | `sandbox.fs.move_files()` | — |
| `delete_file` | `sandbox.fs.delete_file()` | MCP implements this as shell `rm -rf` (no path safety) |
| `get_file_info` | `sandbox.fs.get_file_info()` | — |
| `preview_link` | `sandbox.get_preview_link(port)` | MCP can also curl-check the server first |

## What ONLY the SDK can do (the superset — this is where the Skill earns its keep)

- **Persistent exec sessions** — `process.create_session`, `execute_session_command`,
  `get_session(_command_logs)`, `list_sessions`, `delete_session`. (MCP exec is stateless.)
- **`process.code_run`** — run code in the language runtime with `CodeRunParams`, capture chart
  artifacts. (No MCP equivalent.)
- **Snapshots** — `daytona.snapshot.create/list/get/activate/delete` + the `Image` builder. (MCP
  only *consumes* a snapshot name.)
- **Volumes lifecycle** — `daytona.volume.create/get/list/delete` + `VolumeMount`. (MCP only
  attaches existing volumes at create.)
- **Sandbox lifecycle beyond delete** — `start`, `stop`, `archive`, `get`, `list`. (MCP has only
  create + destroy.)
- **Rich filesystem** — `find_files`, `search_files`, `replace_in_files`, `set_file_permissions`,
  batch + streaming transfer. (MCP has the 7 basic file ops only.)
- **Full git** — `add/commit/push/pull/status/branches/create_branch/checkout_branch/delete_branch`.
- **Computer-use** (`sandbox.computer_use`) and **LSP** (`sandbox.create_lsp_server`). (No MCP tools.)
- **Async API** (`AsyncDaytona`, …) and `get_preview_link().token` for private-sandbox auth.

## Decision rule

- Running in an environment where you can execute Python (Claude Code, an agent runtime, a Daytona
  sandbox)? → **Use the SDK.** It's current, complete, token-cheap (this Skill is ~100 idle tokens
  vs. 12 always-loaded tool schemas), and it's a strict superset.
- No code execution, but the `daytona-mcp` server is connected? → use the **MCP tools**
  (fully-qualified, e.g. `daytona-mcp:execute_command`) for the basic create→exec→files→preview loop.
- Terminal only, no Python? → the **`daytona` CLI**.

The MCP and this Skill are **complementary layers**, not substitutes: MCP is the connection;
the Skill is the know-how for driving Daytona well.
