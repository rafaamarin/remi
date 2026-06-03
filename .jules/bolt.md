
## 2024-05-18 - Textual UI Thread Blocking I/O
**Learning:** During Textual `on_mount`, executing `Path.rglob` (inside `scan_libraries`) synchronously causes the main application thread to block. If the project root has deep directories, the UI initialization will noticeably stall. We must be cautious about hidden generators becoming synchronous when passed to `call_from_thread`.
**Action:** When offloading directory scanning or file system I/O to a worker using `@work(thread=True)`, ensure generators or iterables are fully evaluated into a `list` (or another structure) _inside_ the worker thread before sending them via `call_from_thread` to the main UI thread.
