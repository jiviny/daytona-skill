# Sandboxes: create, configure, snapshot, persist, destroy

Contents:
- [Client setup & auth](#client-setup--auth)
- [Create a sandbox](#create-a-sandbox)
- [Resources](#resources)
- [Auto-stop / auto-archive / auto-delete](#auto-management)
- [Lifecycle: start / stop / archive / delete](#lifecycle)
- [Get / list sandboxes](#get--list)
- [Snapshots (fast reusable environments)](#snapshots)
- [Volumes (persistent storage)](#volumes)
- [Network restrictions](#network-restrictions)
- [CLI equivalents](#cli-equivalents)

## Client setup & auth

```python
from daytona import Daytona, DaytonaConfig

daytona = Daytona()  # reads DAYTONA_API_KEY (required), DAYTONA_API_URL, DAYTONA_TARGET from env

# or explicit:
daytona = Daytona(DaytonaConfig(api_key="...", api_url="https://app.daytona.io/api", target="us"))
```
Async equivalents exist for everything: `AsyncDaytona`, `AsyncSandbox`, `Async*` services.

## Create a sandbox

```python
# Simplest — default image/snapshot:
sandbox = daytona.create()

# From an image, with a language runtime and explicit resources:
from daytona import CreateSandboxFromImageParams, Resources, Image

sandbox = daytona.create(
    CreateSandboxFromImageParams(
        image=Image.debian_slim("3.12").pip_install("numpy"),  # or image="python:3.12"
        language="python",
        resources=Resources(cpu=2, memory=4, disk=10, gpu=0),   # memory/disk in GB
        os_user="daytona",
        env_vars={"FOO": "bar"},
        public=True,
        volumes=None,
    ),
    timeout=120,
    on_snapshot_create_logs=lambda chunk: print(chunk, end=""),
)

# From a pre-built snapshot (do NOT also pass resources — see below):
from daytona import CreateSandboxFromSnapshotParams
sandbox = daytona.create(CreateSandboxFromSnapshotParams(
    snapshot="my-snapshot", env_vars={"FOO": "bar"}, labels={"team": "ai"},
    auto_stop_interval=15, auto_archive_interval=10080, auto_delete_interval=-1,
))
```

`Daytona.create(params=None, *, timeout=60, on_snapshot_create_logs=None) -> Sandbox`

## Resources

`Resources(cpu, memory, disk, gpu, gpu_type)` — `memory`/`disk` are in **GB**.
- The SDK imposes no hard caps documented; your plan/quota does.
- **You cannot pass `resources` together with a `snapshot`** — a snapshot already fixes its
  resource profile. Choose one or the other.
- Note: the bundled MCP `create_sandbox` tool caps cpu≤4, gpu≤1, memory≤8GB, disk≤10GB. The SDK
  is the way to go beyond those.

## Auto-management

Set at create time (minutes); also readable as sandbox attributes of the same name:
- `auto_stop_interval` — idle minutes before the sandbox stops. Default **15**. `0` disables (stays running — costs money).
- `auto_archive_interval` — minutes stopped before archiving. Default **10080** (7 days).
- `auto_delete_interval` — minutes before deletion. Default **-1** (disabled). `0` = delete immediately on stop.

Prefer a short `auto_stop_interval` over leaving sandboxes running. Prefer explicit
`sandbox.delete()` when the task is done.

## Lifecycle

```python
sandbox.start(timeout=60)
sandbox.stop(timeout=60, force=False)
sandbox.archive()                 # state preserved, fully inactive
sandbox.delete(timeout=60)        # destroy; or daytona.delete(sandbox)
```

## Get / list

```python
sb = daytona.get("sandbox-id-or-name")
for sb in daytona.list():         # Iterator[Sandbox]; accepts ListSandboxesQuery
    print(sb.id)
```

## Snapshots

A snapshot is a pre-built image+resource template. Build once, create many fast-booting
sandboxes from it. (The MCP can only *consume* a snapshot name; only the SDK can create one.)

```python
from daytona import CreateSnapshotParams, Image, Resources

image = Image.debian_slim("3.12").pip_install("numpy", "pandas")
daytona.snapshot.create(
    CreateSnapshotParams(name="ds-base", image=image, resources=Resources(cpu=2, memory=4)),
    on_logs=lambda c: print(c, end=""),
)
daytona.snapshot.list(page=1, limit=20)
snap = daytona.snapshot.get("ds-base")
daytona.snapshot.activate(snap)
daytona.snapshot.delete(snap)
```

## Volumes

Persist data across sandboxes without keeping one alive.

```python
from daytona import CreateSandboxFromImageParams, VolumeMount

vol = daytona.volume.get("datasets", create=True)   # get-or-create
daytona.volume.list(); daytona.volume.create("v2"); daytona.volume.delete(vol)

sandbox = daytona.create(CreateSandboxFromImageParams(
    image="python:3.12",
    volumes=[VolumeMount(volume_id=vol.id, mount_path="/data")],  # subpath optional
))
```

## Network restrictions

Lock down egress for untrusted code at create time:
- `network_block_all=True` — block all outbound network.
- `network_allow_list="github.com,pypi.org"` — comma-separated allowlist of domains.

(Field names mirror the MCP's `networkBlockAll` / `networkAllowList`.)

## CLI equivalents

```bash
daytona create [--cpu N --memory N --disk N --target us --env K=V --label k=v --auto-stop 15]
daytona list
daytona info <id>
daytona start <id> | daytona stop <id> | daytona delete <id>
daytona snapshot create|list|push|delete
daytona volume create|list|get|delete
```
The CLI has no first-class per-sandbox file upload/download; use the SDK `fs` module (see
`files.md`) or `daytona exec` for that.
