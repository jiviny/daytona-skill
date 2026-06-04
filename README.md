# Daytona Agent Skills for Claude

A [Claude Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
that teaches Claude **how to drive Daytona** — secure, elastic sandboxes for running AI-generated
code. It is the procedural-knowledge layer that sits on top of Daytona's existing connectivity
(the Python/TypeScript SDK, the `daytona` CLI, and the `daytona-mcp` server).

## Why a Skill (and not just the MCP)?

The Daytona **MCP server** is the *connection* — 12 thin, stateless tools over Daytona's API.
A **Skill** is the *know-how*: when to spin up a sandbox, how to chain a build when `exec` is
stateless, when to snapshot, how to expose a preview, and to always clean up. They're
complementary layers, per [Anthropic's own guidance](https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers):

> "If you're explaining **how** to do something, that's a skill. If you need Claude to
> **access** something, that's MCP."

The Skill also drives the **Python SDK**, which is a strict superset of the MCP's 12 tools
(sessions, `code_run`, snapshots, volumes, full git, rich filesystem, lifecycle, computer-use,
LSP), and it costs ~100 tokens of context when idle versus a dozen tool schemas loaded into
every conversation. See [`skills/daytona-sandbox/reference/sdk-vs-mcp.md`](skills/daytona-sandbox/reference/sdk-vs-mcp.md)
for the full map.

## Launch post & diagram

A short launch post, *"Skills vs MCPs,"* lives in [`blog/`](blog/) ([source](blog/skills-vs-mcps.tex) · [compiled PDF](blog/skills-vs-mcps.pdf)). Its central diagram — the "capability cake," where MCP and Skills are *different layers*, not competitors — is available standalone in [`blog/diagram/`](blog/diagram/) (TikZ source + PDF + PNG):

![Capability cake: Foundation model → MCP → Skills → Agent that ships](blog/diagram/cake.png)

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # plugin registry (publish this repo as a marketplace)
└── skills/
    └── daytona-sandbox/
        ├── SKILL.md              # entrypoint: overview + lifecycle playbook + links
        ├── LICENSE.txt
        ├── reference/            # loaded on demand (progressive disclosure)
        │   ├── sandboxes.md      # create / configure / snapshot / volumes / destroy
        │   ├── exec.md           # commands, code_run, sessions, env, git
        │   ├── files.md          # filesystem operations
        │   ├── preview.md        # preview links
        │   └── sdk-vs-mcp.md     # what the MCP covers vs the SDK superset
        ├── examples/
        │   ├── run-python.md
        │   └── clone-and-test.md
        └── scripts/              # executed via bash; code never enters context
            ├── healthcheck.py    # verify DAYTONA_API_KEY + connectivity
            └── run_in_sandbox.py # deterministic create -> run -> destroy helper
```

## Prerequisites

- A Daytona API key: set `DAYTONA_API_KEY` in the environment (get one at https://app.daytona.io),
  or run `daytona login`.
- Python with the SDK for the bundled scripts: `pip install daytona`.

## Install

### Claude Code (via plugin marketplace)

```bash
/plugin marketplace add daytonaio/claude-skills      # this repo
/plugin install daytona-sandbox@daytona-skills
```

### Claude Code (local, for development/testing)

Copy or symlink the skill into a skills directory Claude Code reads:

```bash
# project-scoped (this repo only):
mkdir -p .claude/skills && cp -r skills/daytona-sandbox .claude/skills/
# or personal (all projects):
cp -r skills/daytona-sandbox ~/.claude/skills/
```

Then verify it's picked up with `/skills`, or invoke directly with `/daytona-sandbox`.

### claude.ai / Claude API

- claude.ai: zip the `skills/daytona-sandbox` folder and upload via Settings → Capabilities → Skills.
- API: upload via the `/v1/skills` endpoints (workspace-wide).

> Note: Skills don't sync across surfaces — install on each surface you use. Bundled scripts
> need a code-execution environment **with network access** (Claude Code has it; the bare Claude
> API surface does not — there, use the `daytona-mcp` server instead).

## Verify

```bash
python3 skills/daytona-sandbox/scripts/healthcheck.py
```

## License

Apache-2.0. See [`skills/daytona-sandbox/LICENSE.txt`](skills/daytona-sandbox/LICENSE.txt).
