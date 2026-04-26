"""Punto de entrada principal para REMI."""

import queue
import sys

from src.core.sampler import SamplerCore
from src.core.interface import EventQueue
from src.ui.app import RemiApp


def main() -> None:
    """Inicializa y arranca la aplicación REMI."""
    # Cola thread-safe para comunicar Pygame (productor) -> Textual (consumidor)
    event_queue: EventQueue = queue.Queue(maxsize=256)
    
    # Inicializar Pygame en su hilo (Core)
    sampler = SamplerCore(event_queue=event_queue)
    sampler.start()
    
    # Inicializar Textual en el hilo principal (UI)
    app = RemiApp(sampler=sampler, event_queue=event_queue)
    
    try:
        # Ejecuta la TUI bloqueando el hilo principal hasta que se cierre
        app.run()
    finally:
        # Garantizar que Pygame limpia recursos y threads
        sampler.stop()


if __name__ == "__main__":
    main()
