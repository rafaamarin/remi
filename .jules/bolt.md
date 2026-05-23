## 2025-02-18 - Async IO for UI Rendering in Textual
**Learning:** In the Textual framework, running synchronous I/O operations (like deep file scanning `Path.rglob`) during component loading (`on_mount`) blocks the main thread, visibly freezing the UI or preventing it from rendering immediately.
**Action:** Always wrap heavy I/O tasks within Textual UI components in a background worker thread using `@work(thread=True)` and use `call_from_thread()` to safely perform subsequent UI/DOM updates.
