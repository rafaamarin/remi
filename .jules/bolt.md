## 2024-05-17 - Textual UI blocking on `Path.rglob`
**Learning:** Using unbounded deep directory scanning like `Path.rglob` during the initial Textual UI loading phase can synchronously block the main thread and cause significant performance bottlenecks, especially when dealing with deeply nested user directories.
**Action:** Use a bounded recursive scan (e.g., `os.walk` with a max depth limit like 2 levels) instead of `Path.rglob` when discovering files on the main thread to preserve necessary nested file discovery without unbounded performance risks.
