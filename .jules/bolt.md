## 2025-02-28 - [Textual Main Thread Blocking]
**Learning:** Running unbounded file I/O such as `scan_libraries` (which uses `rglob`) in the main thread during UI startup (e.g. `on_mount`) causes the UI to freeze until scanning completes.
**Action:** Always move heavy I/O operations in Textual apps to background threads using `@work(thread=True)` and push updates to the UI thread via `call_from_thread`.
