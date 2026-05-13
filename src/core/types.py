from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal

PadId = Literal["PAD1", "PAD2", "PAD3", "PAD4", "PAD5", "PAD6", "PAD7", "PAD8", "PAD9"]

PAD_IDS: Final[tuple[PadId, ...]] = (
    "PAD1", "PAD2", "PAD3",
    "PAD4", "PAD5", "PAD6",
    "PAD7", "PAD8", "PAD9"
)


class PadState(Enum):
    PRESSED = "pressed"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class PadEvent:
    """Evento de pad emitido por la capa core hacia el consumidor (UI/tests)."""

    pad_id: PadId
    state: PadState
    timestamp_ms: int
