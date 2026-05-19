
## 2026-05-19 - Unbounded Directory Scanning Bottleneck
**Learning:** In the TUI initialization phase, using unbounded recursive deep directory scanning (like `Path.rglob`) can synchronously block the main thread. This app's architecture loads the TUI frontend which discovers assets synchronously during its startup. Unbounded disk I/O at this stage leads to unresponsiveness.
**Action:** Replace `rglob` with bounded searches (e.g. `os.walk` with a hard depth limit, e.g. 2 levels) for any UI-blocking directory operations where deep tree traversal isn't strictly necessary.
