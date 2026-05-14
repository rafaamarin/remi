## 2024-05-30 - [Optimize scan_libraries IO bottleneck]
**Learning:** Found a major performance bug in `scan_libraries` where `entry.rglob("*.wav")` recursively scanned the entire file tree for `.wav` files inside every top-level directory in the project root. This caused massive startup latency when projects contained `node_modules` or deep generic directories.
**Action:** Replaced `rglob` with `glob` since `load_kit_from_dir` uses a shallow scan anyway. Keep an eye out for accidentally deep `.rglob()` calls on user-provided or unbounded directories.
