from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal

PadId = Literal["L1", "L2", "R1", "R2"]

PAD_IDS: Final[tuple[PadId, ...]] = ("L1", "L2", "R1", "R2")


class PadState(Enum):
    PRESSED = "pressed"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class PadEvent:
    """Evento de pad emitido por la capa core hacia el consumidor (UI/tests)."""

    pad_id: PadId
    state: PadState
    timestamp_ms: int
