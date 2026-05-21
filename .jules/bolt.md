## 2024-05-21 - [Textual on_mount Blocking by I/O]
**Learning:** Running unbounded synchronous I/O operations (like deep file scanning with `Path.rglob`) directly inside Textual's `on_mount` lifecycle method blocks the main UI thread. This causes the TUI to become completely unresponsive or hang during initialization.
**Action:** Always move potentially slow or unbounded I/O operations into background worker threads using the `@work(thread=True)` decorator in Textual apps, and use `self.call_from_thread()` to safely update the UI components when the background work completes.
