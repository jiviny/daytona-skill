# File operations (sandbox.fs)

Contents:
- [Upload](#upload)
- [Download](#download)
- [List / info](#list--info)
- [Create folder / move / delete](#create-folder--move--delete)
- [Permissions](#permissions)
- [Search & replace (SDK-only)](#search--replace)

All paths are paths **inside the sandbox**. Default scratch location is `/tmp` or the working dir.

## Upload

```python
from daytona import FileUpload

sandbox.fs.upload_file(b"raw bytes", "/tmp/a.txt")     # bytes -> remote path
sandbox.fs.upload_file("local.txt", "/tmp/a.txt")      # local path -> remote path
sandbox.fs.upload_files([FileUpload(...), ...])         # batch
# Streaming with progress/cancel: upload_file_stream(...)
```
Parent directories are created as needed. To write generated text, just pass `bytes`:
`sandbox.fs.upload_file(code.encode(), "/tmp/script.py")`.

## Download

```python
data: bytes = sandbox.fs.download_file("/tmp/a.txt")   # returns bytes
sandbox.fs.download_file("/tmp/a.txt", "local.txt")    # writes to a local path
# Batch / streaming: download_files(...), download_file_stream(...)
```
For images (`.png/.jpg/...`) you get the raw bytes back; decode/base64 as needed.

## List / info

```python
files = sandbox.fs.list_files("/workspace")    # list[FileInfo]
info  = sandbox.fs.get_file_info("/tmp/a.txt") # FileInfo (size, mode, mod time, is_dir, ...)
```

## Create folder / move / delete

```python
sandbox.fs.create_folder("/workspace/new", "0755")   # mode is REQUIRED
sandbox.fs.move_files("/tmp/a.txt", "/tmp/b.txt")     # note: move_files (plural)
sandbox.fs.delete_file("/tmp/a.txt", recursive=False) # set recursive=True for a directory
```
Note: the SDK `delete_file` is a structured FS delete. The MCP's `delete_file` instead shells
out to `rm -rf <path>` with no path safety — another reason to prefer the SDK.

## Permissions

```python
sandbox.fs.set_file_permissions("/tmp/a.txt", mode="0644", owner=None, group=None)
```

## Search & replace

SDK-only, no MCP equivalent — handy for codemods inside a cloned repo:

```python
sandbox.fs.find_files("/workspace", "TODO")              # list[Match] (content search)
sandbox.fs.search_files("/workspace", "*.py")            # SearchFilesResponse (glob)
sandbox.fs.replace_in_files(["/a.py", "/b.py"], "old", "new")  # list[ReplaceResult]
```
