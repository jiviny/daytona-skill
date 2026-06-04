# Preview links (expose a port publicly)

Use this to let the user open a web app / dev server running inside the sandbox.

## Get a preview URL

```python
preview = sandbox.get_preview_link(3000)   # get_preview_link(port: int) -> PortPreviewUrl
print(preview.url)      # public URL routed to that port in the sandbox
print(preview.token)    # access token (needed when the sandbox is private)
```

## The correct flow

1. Start the server **without blocking** the rest of your steps. Run it in the background via a
   session (`run_async=True`) or with `nohup ... &`:
   ```python
   sandbox.process.create_session("web")
   from daytona import SessionExecuteRequest
   sandbox.process.execute_session_command(
       "web", SessionExecuteRequest(command="cd /app && nohup python3 -m http.server 3000 &", run_async=True))
   ```
2. Briefly confirm the server is up (the MCP's `preview_link` does this for you with
   `check_server=True`; with the SDK, curl it yourself):
   ```python
   sandbox.process.exec("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 --max-time 3")
   ```
3. Get and return the preview URL:
   ```python
   url = sandbox.get_preview_link(3000).url
   ```
4. If the sandbox is **public** (`public=True` at create) the URL is open; otherwise include the
   `.token` for access. Never print the token to a shared/log channel unnecessarily.

## Notes

- One preview URL per port; expose multiple ports for multiple services.
- A stopped/auto-stopped sandbox's preview URL goes dead — keep it running (or raise
  `auto_stop_interval`) while the user is viewing.
- MCP equivalent: `daytona-mcp:preview_link` with `port`, `description`, `check_server`.
