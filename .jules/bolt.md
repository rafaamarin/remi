## 2024-05-24 - Async Library Scanning in Textual UI
**Learning:** In Textual UI applications, running bounded/unbounded file scanning operations (`Path.rglob`) directly inside `on_mount` can block the main UI thread during startup.
**Action:** Always move potentially expensive I/O operations to a background worker thread (`@work(thread=True)`) and update the UI asynchronously via `call_from_thread()` to keep the initial load fast and non-blocking.
