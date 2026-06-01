## 2024-06-01 - [Offload unbounded I/O to background worker in Textual]
**Learning:** Unbounded I/O operations (like deep file scanning with `Path.rglob`) can block the main UI thread during initial loading (e.g., `on_mount`), causing the Textual UI to stutter or freeze.
**Action:** Always offload potentially expensive I/O operations to a background worker thread using `@work(thread=True)` and safely update the UI via `call_from_thread()`. Ensure the result is fully evaluated (e.g., cast to a list) within the worker thread before passing it back to the UI thread.
