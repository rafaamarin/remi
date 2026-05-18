## 2025-03-03 - Bounded Depth Scanning for Initial Loading
**Learning:** Using `Path.rglob` for discovering assets in deep folder structures causes unbounded synchronous blocking on the main thread during Textual UI initialization.
**Action:** Replace `rglob` with `os.walk` specifying a maximum depth (e.g., `max_depth=2`) when a shallow scan is sufficient.
