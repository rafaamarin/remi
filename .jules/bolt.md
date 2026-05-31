## 2024-05-31 - Unbounded I/O in Textual on_mount

**Learning:** Deep file scanning (`Path.rglob`) inside Textual's `on_mount` lifecycle method blocks the main UI thread, causing the application to "hang" before rendering. This is especially problematic for operations that scale with the user's filesystem. Even if `scan_libraries` returns a list, the underlying `rglob` operation itself is synchronous and I/O bound.

**Action:** Move potentially unbounded I/O operations from `on_mount` into a background worker (`@work(thread=True)`). Evaluate any iterators/generators completely within the worker thread, then pass the fully resolved result (e.g., `list`) to `call_from_thread` to update the UI components safely without blocking the main event loop.
