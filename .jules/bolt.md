## 2024-05-16 - Avoid rglob blocking on main thread
**Learning:** During the initial Textual UI loading phase, deep directory scanning using `Path.rglob` for asset discovery can cause severe synchronous blocking of the main thread, especially if user directories contain deep hierarchies or large numbers of unrelated files.
**Action:** Prefer shallow scanning (`Path.glob`) when traversing user directories to discover kits or assets. The loading behavior should be consistent with shallow kit loading structure.
