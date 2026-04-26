from __future__ import annotations

import queue
from typing import Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static
from textual.worker import get_current_worker

from src.core.interface import EventQueue, SamplerInterface
from src.core.types import PAD_IDS, PadEvent, PadId, PadState


class DrumPad(Static):
    """Widget que representa un pad en la UI."""
    
    pad_id: reactive[str] = reactive("UNK")
    is_pressed: reactive[bool] = reactive(False)
    
    def __init__(self, pad_id: PadId) -> None:
        super().__init__(pad_id, id=f"pad-{pad_id}")
        self.pad_id = pad_id

    def watch_is_pressed(self, old_val: bool, new_val: bool) -> None:
        if new_val:
            self.add_class("pressed")
        else:
            self.remove_class("pressed")


class RemiApp(App[None]):
    """App principal de la TUI de REMI."""

    CSS = """
    Screen {
        align: center middle;
    }

    #pad-grid {
        grid-size: 2 2;
        grid-gutter: 2 4;
        width: 60;
        height: 20;
        margin: 2;
    }

    DrumPad {
        content-align: center middle;
        height: 100%;
        width: 100%;
        border: thick $background 80%;
        background: $surface;
        color: $text;
        text-style: bold;
    }

    /* Colores por defecto para cada pad */
    #pad-L1 { background: $panel; }
    #pad-R1 { background: $panel; }
    #pad-L2 { background: $panel; }
    #pad-R2 { background: $panel; }

    /* Estado presionado */
    DrumPad.pressed {
        background: $accent;
        color: $text;
        border: thick $accent-darken-2;
    }
    """

    BINDINGS: ClassVar[Any] = [
        ("q", "trigger_pad('L1')", "Pad L1"),
        ("w", "trigger_pad('R1')", "Pad R1"),
        ("a", "trigger_pad('L2')", "Pad L2"),
        ("s", "trigger_pad('R2')", "Pad R2"),
        ("escape", "quit", "Salir"),
    ]

    def __init__(
        self,
        sampler: SamplerInterface,
        event_queue: EventQueue,
    ) -> None:
        super().__init__()
        self._sampler = sampler
        self._event_queue = event_queue
        self._pads: dict[PadId, DrumPad] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Grid(id="pad-grid"):
            for pad_id in PAD_IDS:
                pad = DrumPad(pad_id)
                self._pads[pad_id] = pad
                yield pad
        yield Footer()

    def on_mount(self) -> None:
        self.title = "REMI - Low Latency MIDI Sampler"
        if self._sampler.has_joystick:
            self.sub_title = "Hardware: Joystick detectado"
        else:
            self.sub_title = "Hardware: Teclado (Q/W/A/S)"
            
        # Iniciar el worker que drena la cola de eventos de Pygame
        self._poll_sampler_events()

    @work(exclusive=True, thread=True)
    def _poll_sampler_events(self) -> None:
        """Worker en segundo plano para leer la cola thread-safe sin bloquear la UI."""
        worker = get_current_worker()
        while not worker.is_cancelled:
            try:
                # Bloqueo con timeout para permitir revisar is_cancelled
                event: PadEvent = self._event_queue.get(timeout=0.1)
                # Enviar al hilo principal de UI de forma segura
                self.call_from_thread(self._handle_pad_event, event)
            except queue.Empty:
                continue

    def _handle_pad_event(self, event: PadEvent) -> None:
        """Actualiza la UI basado en el evento (corre en el hilo principal)."""
        pad = self._pads.get(event.pad_id)
        if pad is not None:
            pad.is_pressed = event.state == PadState.PRESSED

    def action_trigger_pad(self, pad_id: PadId) -> None:
        """Dispara el pad desde el teclado (UI fallback).
        Textual captura las teclas de forma asíncrona, y enviamos el trigger a Pygame."""
        # Enviamos PRESSED
        self._sampler.trigger_pad(pad_id, PadState.PRESSED)
        # Programamos el RELEASED después de 100ms para simular el toque en UI
        self.set_timer(0.1, lambda: self._sampler.trigger_pad(pad_id, PadState.RELEASED))
