from __future__ import annotations

import queue
from typing import Callable, Protocol

from src.core.types import PadEvent, PadId, PadState

EventCallback = Callable[[PadEvent], None]
EventQueue = queue.Queue[PadEvent]


class SamplerInterface(Protocol):
    """Contrato de la capa core (audio + hardware) hacia consumidores externos.

    === Modelo de threading ===
    - El productor de eventos corre en un thread propio (polling síncrono de pygame).
    - El consumidor (Textual) corre en el main thread con asyncio.
    - La comunicación va SIEMPRE por uno de estos dos canales, ambos thread-safe:
        (a) ``event_queue`` pasado al constructor — preferido para Textual.
            El consumidor drena con un Worker y marshala a la UI vía
            ``app.call_from_thread(...)``.
        (b) ``on_event`` callback — atajo para tests y scripts.
            CORRE EN EL THREAD DEL PRODUCTOR. Prohibido bloquear o hacer I/O.

    === GIL ===
    - El thread de polling pasa >95% del ciclo dormido en ``pygame.time.Clock.tick``,
      con el GIL liberado. pygame-ce libera el GIL en sus llamadas C
      (event.pump, joystick.get_*, mixer.Sound.play). El cuello de botella real es
      el buffer del mixer (512 samples ≈ 11.6 ms), no la contención del GIL.

    === Idempotencia / edge detection ===
    - ``trigger_pad`` y el polling interno deduplican: solo se emite evento y se
      reproduce sonido en transición de estado (False→True para PRESSED,
      True→False para RELEASED). Llamadas repetidas con el mismo estado son no-op.

    === Volumen por pad ===
    - Cada pad tiene un volumen independiente en el rango ``[0.0, 1.0]``.
    - Tras ``start()`` todos los pads arrancan en ``1.0``.
    - ``set_pad_volume`` es thread-safe y se clampa al rango. El cambio aplica
      a triggers futuros Y a instancias actualmente en reproducción
      (``pygame.mixer.Sound.set_volume`` es retroactivo).

    === Ciclo de vida ===
    - ``start()`` debe llamarse exactamente una vez antes de cualquier otro método.
    - ``stop()`` es idempotente.
    """

    @property
    def has_joystick(self) -> bool:
        """True si se detectó mando físico al arrancar; False → modo fallback."""
        ...

    def start(self) -> None:
        """Inicializa mixer, carga assets, detecta joystick, lanza thread de polling."""
        ...

    def stop(self) -> None:
        """Detiene thread, libera mixer y joystick. Idempotente."""
        ...

    def trigger_pad(self, pad_id: PadId, state: PadState) -> None:
        """Inyecta un evento de input desde fuera (UI Textual, tests).

        Thread-safe. Aplica edge detection: si el pad ya estaba en ``state``, no-op.
        """
        ...

    def get_pad_volume(self, pad_id: PadId) -> float:
        """Volumen actual del pad en ``[0.0, 1.0]``. Default tras ``start()``: ``1.0``."""
        ...

    def set_pad_volume(self, pad_id: PadId, volume: float) -> None:
        """Asigna volumen del pad. Thread-safe. Se clampa a ``[0.0, 1.0]``.

        Aplica tanto a triggers futuros como a cualquier instancia ya sonando
        del mismo pad.
        """
        ...
