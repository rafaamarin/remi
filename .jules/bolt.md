## 2024-05-24 - [Unbounded I/O in Textual UI]
**Learning:** Unbounded I/O operations (like `Path.rglob`) during the initial Textual UI loading phase (`on_mount`) can block the main thread, resulting in a sluggish startup.
**Action:** Move these operations into a Textual background worker thread (`@work(thread=True)`) and update the UI safely via `call_from_thread()`.
