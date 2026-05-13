"""Tonos sintéticos en RAM para que el sampler corra standalone sin assets/.

Snippet del usuario reproducido verbatim. Se usa solo como fallback cuando
no se inyectan assets reales al constructor de ``SamplerCore``.
"""

from __future__ import annotations

import io
import math
import struct
import wave

from src.core.types import PadId


def generar_tono_en_memoria(frecuencia: float, duracion_ms: int) -> io.BytesIO:
    """Genera un WAV en memoria RAM sin tocar el disco duro."""
    sample_rate = 44100
    n_samples = int(sample_rate * (duracion_ms / 1000.0))
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            t = float(i) / sample_rate
            valor = int(32767.0 * math.sin(2.0 * math.pi * frecuencia * t))
            decay = 1.0 - (i / n_samples)
            valor = int(valor * decay)
            data = struct.pack('<h', valor)
            wav_file.writeframesraw(data)
    buffer.seek(0)
    return buffer


DUMMY_ASSETS: dict[PadId, io.BytesIO] = {
    "PAD1": generar_tono_en_memoria(60.0, 150),    # Bombo
    "PAD2": generar_tono_en_memoria(200.0, 100),   # Caja
    "PAD3": generar_tono_en_memoria(400.0, 120),   # Tom alto
    "PAD4": generar_tono_en_memoria(8000.0, 50),   # Hi-Hat Cerrado
    "PAD5": generar_tono_en_memoria(4000.0, 250),  # Hi-Hat Abierto
    "PAD6": generar_tono_en_memoria(300.0, 150),   # Tom medio
    "PAD7": generar_tono_en_memoria(800.0, 80),    # Cencerro
    "PAD8": generar_tono_en_memoria(6000.0, 400),  # Crash
    "PAD9": generar_tono_en_memoria(100.0, 200),   # Tom base
}
