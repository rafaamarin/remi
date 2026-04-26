"""Implementación pygame-ce del contrato ``SamplerInterface``.

Este módulo SÍ depende de pygame. Importarlo carga SDL en memoria.
La UI Textual debe importar el contrato desde ``src.core`` (sin pygame) y
recibir una instancia de ``SamplerCore`` por inyección de dependencia.
"""

from __future__ import annotations

import io
import os
import queue
import threading
from typing import Final

import pygame

from src.core._dummy_assets import DUMMY_ASSETS
from src.core.interface import EventCallback, EventQueue
from src.core.types import PAD_IDS, PadEvent, PadId, PadState

# === Constantes de hardware (DualShock4 sobre SDL2 + Linux) ===
# Si los IDs no funcionan en tu driver concreto, ejecuta
# `python -m pygame.examples.joystick` y ajusta.
DS4_BUTTON_L1: Final[int] = 9
DS4_BUTTON_R1: Final[int] = 10
DS4_AXIS_L2: Final[int] = 4
DS4_AXIS_R2: Final[int] = 5

TRIGGER_THRESHOLD: Final[float] = 0.5

# Latencia máxima que tarda ``stop()`` en propagarse al thread de polling cuando
# no llegan eventos de hardware. ``event.wait`` duerme hasta este límite con el
# GIL liberado y la CPU al 0 %.
EVENT_WAIT_TIMEOUT_MS: Final[int] = 100

# Mapeos derivados (los IDs de PadId nunca caen fuera de PAD_IDS).
_BUTTON_TO_PAD: Final[dict[int, PadId]] = {
    DS4_BUTTON_L1: "L1",
    DS4_BUTTON_R1: "R1",
}
_AXIS_TO_PAD: Final[dict[int, PadId]] = {
    DS4_AXIS_L2: "L2",
    DS4_AXIS_R2: "R2",
}
_KEY_TO_PAD: Final[dict[int, PadId]] = {
    pygame.K_q: "L1",
    pygame.K_w: "R1",
    pygame.K_a: "L2",
    pygame.K_s: "R2",
}

# === Constantes del mixer ===
MIXER_FREQUENCY: Final[int] = 44100
MIXER_SIZE: Final[int] = -16
MIXER_CHANNELS: Final[int] = 2
MIXER_BUFFER: Final[int] = 512  # ~11.6 ms @ 44.1 kHz one-way

# Stack de audio preferido en Linux moderno (SDL2 lo respeta como lista de
# fallbacks separada por comas). No sobreescribimos si el entorno ya lo fija
# (p. ej. ``SDL_AUDIODRIVER=dummy`` en CI/tests).
_DEFAULT_SDL_AUDIODRIVER: Final[str] = "pipewire,pulseaudio,alsa"


class SamplerCore:
    """Sampler MIDI 2x2 con polling síncrono y emisión thread-safe.

    Cumple ``SamplerInterface`` por duck typing. Ver ese Protocol para el
    contrato normativo de threading, GIL, edge detection y volumen.

    Args:
        assets: dict ``{pad_id: BytesIO de un WAV}``. Si es ``None``, usa
            ``DUMMY_ASSETS`` (4 tonos sintéticos en RAM).
        event_queue: cola thread-safe a drenar desde la UI. Recomendado
            ``queue.Queue(maxsize=256)``: si se llena, los eventos nuevos
            se descartan silenciosamente (preferimos perder eventos antes
            que bloquear el thread de polling).
        on_event: callback alternativo. CORRE EN EL THREAD DE POLLING —
            prohibido bloquear o hacer I/O dentro.
    """

    def __init__(
        self,
        assets: dict[PadId, io.BytesIO] | None = None,
        event_queue: EventQueue | None = None,
        on_event: EventCallback | None = None,
    ) -> None:
        self._assets: dict[PadId, io.BytesIO] = assets if assets is not None else DUMMY_ASSETS
        self._event_queue = event_queue
        self._on_event = on_event

        self._lock = threading.Lock()
        self._pad_states: dict[PadId, bool] = {pad: False for pad in PAD_IDS}
        self._volumes: dict[PadId, float] = {pad: 1.0 for pad in PAD_IDS}
        self._sounds: dict[PadId, pygame.mixer.Sound] = {}

        self._joystick: pygame.joystick.JoystickType | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    @property
    def has_joystick(self) -> bool:
        return self._joystick is not None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return

        # Forzar el stack de audio moderno en Linux antes de tocar SDL.
        os.environ.setdefault("SDL_AUDIODRIVER", _DEFAULT_SDL_AUDIODRIVER)

        # pre_init DEBE preceder a pygame.init() para fijar el buffer pequeño.
        # allowedchanges=0 prohíbe que SDL renegocie ningún parámetro a nuestras
        # espaldas — preferimos que falle a que el mixer arranque con buffer 1024.
        pygame.mixer.pre_init(
            MIXER_FREQUENCY,
            MIXER_SIZE,
            MIXER_CHANNELS,
            MIXER_BUFFER,
            allowedchanges=0,
        )
        pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init(
                MIXER_FREQUENCY,
                MIXER_SIZE,
                MIXER_CHANNELS,
                MIXER_BUFFER,
                allowedchanges=0,
            )

        pygame.joystick.init()

        # Blindar la cola de eventos de SDL de basura irrelevante nativamente:
        # Esto previene saturación de RAM/CPU y permite coexistencia con Textual.
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYDEVICEADDED,
            pygame.JOYDEVICEREMOVED,
            pygame.QUIT,
            pygame.KEYDOWN,
            pygame.KEYUP,
        ])

        if pygame.joystick.get_count() > 0:
            try:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
            except pygame.error:
                pass

        for pad_id, buf in self._assets.items():
            buf.seek(0)
            sound = pygame.mixer.Sound(buffer=buf.read())
            sound.set_volume(self._volumes[pad_id])
            self._sounds[pad_id] = sound

        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="SamplerCore-Poll",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._running and self._thread is None:
            return

        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        self._sounds.clear()

        if self._joystick is not None:
            self._joystick.quit()
            self._joystick = None

        if pygame.joystick.get_init():
            pygame.joystick.quit()
        if pygame.mixer.get_init():
            pygame.mixer.quit()

    def trigger_pad(self, pad_id: PadId, state: PadState) -> None:
        new_pressed = state == PadState.PRESSED
        with self._lock:
            if self._pad_states[pad_id] == new_pressed:
                return  # edge detection: sin transición, no-op
            self._pad_states[pad_id] = new_pressed
        self._handle_transition(pad_id, state)

    def get_pad_volume(self, pad_id: PadId) -> float:
        with self._lock:
            return self._volumes[pad_id]

    def set_pad_volume(self, pad_id: PadId, volume: float) -> None:
        clamped = max(0.0, min(1.0, volume))
        with self._lock:
            self._volumes[pad_id] = clamped
            sound = self._sounds.get(pad_id)
        if sound is not None:
            # set_volume es retroactivo: aplica a instancias ya sonando.
            sound.set_volume(clamped)

    def _handle_transition(self, pad_id: PadId, state: PadState) -> None:
        if state == PadState.PRESSED:
            sound = self._sounds.get(pad_id)
            if sound is not None:
                sound.play()
        self._emit_event(
            PadEvent(
                pad_id=pad_id,
                state=state,
                timestamp_ms=pygame.time.get_ticks(),
            )
        )

    def _emit_event(self, event: PadEvent) -> None:
        if self._event_queue is not None:
            try:
                self._event_queue.put_nowait(event)
            except queue.Full:
                pass  # consumidor lento: descartamos antes que bloquear polling
        if self._on_event is not None:
            self._on_event(event)

    def _poll_loop(self) -> None:
        # Event-driven puro: bloqueamos en SDL hasta que llegue un evento o
        # expire el timeout. Unico consumidor de la cola SDL para evitar races.
        while self._running:
            ev = pygame.event.wait(EVENT_WAIT_TIMEOUT_MS)
            if ev.type == pygame.NOEVENT:
                continue
            self._handle_sdl_event(ev)

    def _handle_sdl_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.QUIT:
            self._running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self._running = False
            else:
                pad = _KEY_TO_PAD.get(ev.key)
                if pad is not None:
                    self.trigger_pad(pad, PadState.PRESSED)
        elif ev.type == pygame.KEYUP:
            pad = _KEY_TO_PAD.get(ev.key)
            if pad is not None:
                self.trigger_pad(pad, PadState.RELEASED)
        elif ev.type == pygame.JOYBUTTONDOWN:
            pad = _BUTTON_TO_PAD.get(ev.button)
            if pad is not None:
                self.trigger_pad(pad, PadState.PRESSED)
        elif ev.type == pygame.JOYBUTTONUP:
            pad = _BUTTON_TO_PAD.get(ev.button)
            if pad is not None:
                self.trigger_pad(pad, PadState.RELEASED)
        elif ev.type == pygame.JOYAXISMOTION:
            pad = _AXIS_TO_PAD.get(ev.axis)
            if pad is not None:
                pressed = ev.value >= TRIGGER_THRESHOLD
                self.trigger_pad(
                    pad,
                    PadState.PRESSED if pressed else PadState.RELEASED,
                )
        elif ev.type == pygame.JOYDEVICEADDED:
            # Hotplug in: Reconectar hardware
            if self._joystick is None:
                try:
                    self._joystick = pygame.joystick.Joystick(ev.device_index)
                    self._joystick.init()
                except pygame.error:
                    pass
        elif ev.type == pygame.JOYDEVICEREMOVED:
            # Hotplug out: Limpiar si se desconectó el activo
            if self._joystick is not None and self._joystick.get_instance_id() == ev.instance_id:
                self._joystick.quit()
                self._joystick = None


def _run_demo() -> None:
    """Demo standalone — abre ventana SDL para capturar Q/W/A/S como fallback."""
    event_queue: EventQueue = queue.Queue(maxsize=256)
    sampler = SamplerCore(event_queue=event_queue)
    sampler.start()

    pygame.display.set_caption("REMI — sampler core demo")
    screen = pygame.display.set_mode((320, 120))
    font = pygame.font.SysFont(None, 18)

    if sampler.has_joystick:
        print("Joystick: detectado — usa L1/L2/R1/R2 del mando")
    else:
        print("Joystick: NO detectado — fallback teclado Q/W/A/S")
    print("ESC o cerrar ventana para salir.\n")

    # El hilo principal ya no lee SDL, todo lo procesa el poll_loop.
    while sampler.is_running:
        while True:
            try:
                pad_event = event_queue.get_nowait()
            except queue.Empty:
                break
            print(pad_event)

        screen.fill((20, 20, 30))
        text = font.render("Q W A S = pads  |  ESC = salir", True, (200, 200, 200))
        screen.blit(text, (10, 50))
        pygame.display.flip()
        pygame.time.wait(16)

    sampler.stop()
    pygame.quit()


if __name__ == "__main__":
    _run_demo()
