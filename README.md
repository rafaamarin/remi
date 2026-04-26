# REMI — Terminal MIDI Sampler

A low-latency polyphonic drum sampler for the terminal. Trigger samples via a DualShock 4 controller or keyboard, manage sound libraries from a TUI sidebar, and remap pads visually — all without leaving the CLI.

![REMI splash](.remi-slant.png)

---

## Features

- **2x2 pad layout** — L1, R1 (top row) and L2, R2 (bottom row), matching DS4 shoulder buttons and triggers
- **DualShock 4 support** — L1/R1 as buttons, L2/R2 as analog triggers (threshold: 0.5)
- **Keyboard fallback** — Q/W/A/S when no joystick is detected
- **Hotplug** — controller connect/disconnect handled at runtime without restart
- **Hot-swap kits** — load a new sound library atomically while the engine is running
- **Library browser** — sidebar lists all directories under the project root; select to load
- **Visual pad mapper** — press `m` to assign WAV files to pads; saved to `remi.json` per kit
- **Sub-12 ms latency** — mixer initialized at 44 100 Hz with a 512-sample buffer before the TUI starts
- **Security** — path traversal protection and per-sample 25 MB OOM guard on asset loading

---

## Requirements

- Python 3.12+
- PipeWire, PulseAudio, or ALSA (Linux)
- A DualShock 4 connected via USB or Bluetooth (optional)

---

## Installation

```bash
git clone https://github.com/rafaamarin/remi.git
cd remi
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Running

```bash
python main.py
```

The TUI starts with a gradient ASCII header, a 2x2 pad grid, and a library sidebar on the right.

---

## Keybindings

| Key       | Action                            |
|-----------|-----------------------------------|
| `Q`       | Trigger pad L1                    |
| `W`       | Trigger pad R1                    |
| `A`       | Trigger pad L2                    |
| `S`       | Trigger pad R2                    |
| `M`       | Open pad mapper for selected kit  |
| `Escape`  | Quit                              |

---

## Sound Libraries

REMI discovers kit directories automatically. Place a folder with `.wav` files in the project root and it will appear in the sidebar. Select it to load.

Included: **Growlybass** — an aggressive sampled electric bass, good for testing transient response across all four pads.

To map specific samples to pads, select the kit in the sidebar and press `M`. The mapping is saved to `remi.json` inside the kit directory.

---

## Architecture

```
main.py              Entry point — wires SamplerCore and RemiApp
src/
  core/
    types.py         PadId, PadState, PadEvent (frozen dataclass)
    interface.py     SamplerInterface Protocol (no pygame dependency)
    sampler.py       SamplerCore — pygame-ce audio + DS4 polling thread
    assets.py        load_kit_from_dir, scan_libraries, save_mapping
  ui/
    app.py           RemiApp (Textual) — grid, sidebar, kit loading worker
    mapping_modal.py MappingModal — visual WAV-to-pad assignment
    splash.py        Splash screen
```

**Threading model:** `SamplerCore` runs a daemon thread (`SamplerCore-Poll`) that blocks on `pygame.event.wait()`, consuming zero CPU while idle. Events are pushed into a `queue.Queue(maxsize=256)` and drained by a Textual worker thread, so neither layer ever blocks the other.

---

## Development

```bash
pip install -e ".[dev]"
mypy src          # strict type checking
pytest            # tests
```

To test the audio engine standalone (without the TUI):

```bash
python -m src.core.sampler
```

Opens a minimal SDL window; use Q/W/A/S or a connected DS4. ESC to exit.

---

## License

MIT.
