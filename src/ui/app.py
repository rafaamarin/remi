from __future__ import annotations

import io
import queue
from pathlib import Path
from typing import Any, ClassVar

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Label, ListItem, ListView, Static
from textual.worker import get_current_worker

from src.core._dummy_assets import DUMMY_ASSETS
from src.core.assets import load_kit_from_dir, save_mapping, scan_libraries
from src.core.interface import EventQueue, SamplerInterface
from src.core.types import PAD_IDS, PadEvent, PadId, PadState
from src.ui.mapping_modal import MappingModal

REMI_ASCII: tuple[str, ...] = (
    "██████╗ ███████╗███╗   ███╗██╗",
    "██╔══██╗██╔════╝████╗ ████║██║",
    "██████╔╝█████╗  ██╔████╔██║██║",
    "██╔══██╗██╔══╝  ██║╚██╔╝██║██║",
    "██║  ██║███████╗██║ ╚═╝ ██║██║",
    "╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝",
)

_GRADIENT_START: tuple[int, int, int] = (0xFF, 0x5E, 0x5B)
_GRADIENT_END: tuple[int, int, int] = (0xFF, 0xB8, 0x6C)


def _ascii_header_text() -> Text:
    text = Text(justify="center")
    n = len(REMI_ASCII)
    for i, line in enumerate(REMI_ASCII):
        t = i / max(n - 1, 1)
        r = int(_GRADIENT_START[0] + (_GRADIENT_END[0] - _GRADIENT_START[0]) * t)
        g = int(_GRADIENT_START[1] + (_GRADIENT_END[1] - _GRADIENT_START[1]) * t)
        b = int(_GRADIENT_START[2] + (_GRADIENT_END[2] - _GRADIENT_START[2]) * t)
        text.append(line + "\n", style=f"bold #{r:02x}{g:02x}{b:02x}")
    text.append("low-latency MIDI sampler · DS4 / QWE ASD ZXC", style="italic dim")
    return text


class AsciiHeader(Static):
    def __init__(self) -> None:
        super().__init__(_ascii_header_text(), id="ascii-header")


class DrumPad(Static):
    is_pressed: reactive[bool] = reactive(False)
    kit_name: reactive[str] = reactive("—")

    def __init__(self, pad_id: PadId) -> None:
        super().__init__(id=f"pad-{pad_id}")
        self._pad_id: PadId = pad_id

    def render(self) -> Text:
        text = Text(justify="center")
        text.append(f"{self._pad_id}\n\n", style="bold")
        text.append(self.kit_name, style="dim italic")
        return text

    def watch_is_pressed(self, _old: bool, new: bool) -> None:
        self.set_class(new, "pressed")

    def watch_kit_name(self, _old: str, _new: str) -> None:
        self.refresh()


class LibraryItem(ListItem):
    """Sidebar row. ``kit_path=None`` represents the synthetic default kit."""

    def __init__(self, kit_path: Path | None) -> None:
        label = "Default" if kit_path is None else kit_path.name
        super().__init__(Label(label))
        self.kit_path: Path | None = kit_path


class RemiApp(App[None]):
    CSS = """
    Screen {
        background: #14161c;
        color: #e6e6e6;
    }

    AsciiHeader {
        height: auto;
        padding: 1 0;
        background: #14161c;
    }

    #body {
        height: 1fr;
    }

    #pad-pane {
        width: 1fr;
        padding: 1 2;
    }

    #lib-pane {
        width: 32;
        padding: 1 2;
        border-left: tall #1c2030;
        background: #14161c;
    }

    #lib-title {
        color: #ffb86c;
        text-style: bold;
        padding-bottom: 1;
        height: auto;
    }

    #pad-grid {
        grid-size: 3 3;
        grid-gutter: 1 3;
        height: 1fr;
        width: 1fr;
    }

    DrumPad {
        content-align: center middle;
        height: 100%;
        width: 100%;
        background: #1c2030;
        color: #e6e6e6;
        border: tall #2a3044;
        text-align: center;
    }

    DrumPad.pressed {
        background: #ff7a45;
        color: #14161c;
        border: tall #ffb86c;
        text-style: bold;
    }

    #kit-label {
        color: #ffb86c;
        text-style: bold;
        padding: 1 0 0 0;
        text-align: center;
        height: auto;
    }

    ListView {
        background: #14161c;
        height: 1fr;
    }

    ListView > ListItem {
        padding: 0 1;
        background: #14161c;
    }

    ListView > ListItem.--highlight {
        background: #2a3044;
        color: #ffb86c;
    }
    """

    BINDINGS: ClassVar[Any] = [
        ("q", "trigger_pad('PAD1')", "PAD1"),
        ("w", "trigger_pad('PAD2')", "PAD2"),
        ("e", "trigger_pad('PAD3')", "PAD3"),
        ("a", "trigger_pad('PAD4')", "PAD4"),
        ("s", "trigger_pad('PAD5')", "PAD5"),
        ("d", "trigger_pad('PAD6')", "PAD6"),
        ("z", "trigger_pad('PAD7')", "PAD7"),
        ("x", "trigger_pad('PAD8')", "PAD8"),
        ("c", "trigger_pad('PAD9')", "PAD9"),
        ("m", "open_mapper", "Mapear Kit"),
        ("escape", "quit", "Salir"),
    ]

    def __init__(
        self,
        sampler: SamplerInterface,
        event_queue: EventQueue,
        project_root: Path | None = None,
    ) -> None:
        super().__init__()
        self._sampler = sampler
        self._event_queue = event_queue
        self._pads: dict[PadId, DrumPad] = {}
        self._project_root = project_root or Path.cwd()

    def compose(self) -> ComposeResult:
        yield AsciiHeader()
        with Horizontal(id="body"):
            with Vertical(id="pad-pane"):
                with Grid(id="pad-grid"):
                    # Row-major: QWE, ASD, ZXC
                    pad_layout: tuple[PadId, ...] = (
                        "PAD1", "PAD2", "PAD3",
                        "PAD4", "PAD5", "PAD6",
                        "PAD7", "PAD8", "PAD9",
                    )
                    for pad_id in pad_layout:
                        pad = DrumPad(pad_id)
                        self._pads[pad_id] = pad
                        yield pad
                yield Static("Kit: Default", id="kit-label")
            with Vertical(id="lib-pane"):
                yield Static("LIBRARIES", id="lib-title")
                yield ListView(id="lib-list")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "REMI"
        self.sub_title = "DS4" if self._sampler.has_joystick else "Teclado QWE/ASD/ZXC"
        self._refresh_libraries()
        self._poll_sampler_events()

    def _refresh_libraries(self) -> None:
        # Bolt: Optimizing application load time
        # Moving the library file system scan to a background worker to prevent
        # blocking the Textual main thread during mount.
        # Expected Impact: Eliminates UI freeze on startup in large project directories.
        self._scan_libraries_worker()

    @work(exclusive=True, thread=True)
    def _scan_libraries_worker(self) -> None:
        """Runs the library scan in a background thread."""
        # Eagerly consume the generator in the background thread to ensure
        # the blocking I/O actually happens here and not on the main thread
        paths = list(scan_libraries(self._project_root))

        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(self._update_library_ui, paths)

    def _update_library_ui(self, paths: list[Path]) -> None:
        """Updates the library UI with scanned paths safely from main thread."""
        list_view = self.query_one("#lib-list", ListView)
        list_view.clear()
        list_view.append(LibraryItem(None))
        for path in paths:
            list_view.append(LibraryItem(path))

    @work(exclusive=True, thread=True)
    def _poll_sampler_events(self) -> None:
        worker = get_current_worker()
        while not worker.is_cancelled:
            try:
                event: PadEvent = self._event_queue.get(timeout=0.1)
                self.call_from_thread(self._handle_pad_event, event)
            except queue.Empty:
                continue

    def _handle_pad_event(self, event: PadEvent) -> None:
        pad = self._pads.get(event.pad_id)
        if pad is not None:
            pad.is_pressed = event.state == PadState.PRESSED

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, LibraryItem):
            self._load_kit_worker(event.item.kit_path)

    @work(exclusive=True, thread=True, group="kit-load")
    def _load_kit_worker(self, kit_path: Path | None) -> None:
        if kit_path is None:
            assets: dict[PadId, io.BytesIO] = DUMMY_ASSETS
            name = "Default"
        else:
            try:
                assets = load_kit_from_dir(kit_path)
            except OSError as exc:
                self.call_from_thread(
                    self.notify,
                    f"No se pudo leer {kit_path.name}: {exc}",
                    severity="error",
                )
                return
            if not assets:
                self.call_from_thread(
                    self.notify,
                    f"Sin samples válidos en {kit_path.name}",
                    severity="warning",
                )
                return
            name = kit_path.name

        try:
            self._sampler.load_kit(assets)
        except Exception as exc:  # pygame puede fallar al decodificar WAV inválidos
            self.call_from_thread(
                self.notify,
                f"Error al cargar el kit: {exc}",
                severity="error",
            )
            return

        self.call_from_thread(self._on_kit_loaded, name)

    def _on_kit_loaded(self, name: str) -> None:
        for pad in self._pads.values():
            pad.kit_name = name
        self.query_one("#kit-label", Static).update(f"Kit: {name}")
        self.notify(f"Kit cargado: {name}", severity="information")

    def action_trigger_pad(self, pad_id: PadId) -> None:
        self._sampler.trigger_pad(pad_id, PadState.PRESSED)
        self.set_timer(
            0.1,
            lambda: self._sampler.trigger_pad(pad_id, PadState.RELEASED),
        )

    def action_open_mapper(self) -> None:
        """Abre el modal de mapeo para el kit seleccionado actualmente."""
        list_view = self.query_one("#lib-list", ListView)
        selected_item = list_view.highlighted_child
        if isinstance(selected_item, LibraryItem) and selected_item.kit_path is not None:
            kit_path_non_none = selected_item.kit_path
            def handle_mapping(mapping: dict[PadId, str] | None) -> None:
                if mapping:
                    # Guardar a disco
                    save_mapping(kit_path_non_none, mapping)
                    # Recargar el kit para aplicar cambios
                    self._load_kit_worker(kit_path_non_none)
                    self.notify("Mapeo guardado y kit recargado.")

            self.push_screen(MappingModal(kit_path_non_none), handle_mapping)
        else:
            self.notify("Selecciona una librería válida para mapear", severity="warning")
