from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from src.core.types import PAD_IDS, PadId


class MappingModal(ModalScreen[dict[PadId, str] | None]):
    """Pantalla modal para asignar archivos .wav a pads."""

    CSS = """
    MappingModal {
        align: center middle;
    }

    #modal-container {
        width: 80%;
        height: 80%;
        background: #1c2030;
        border: thick #2a3044;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        color: #ffb86c;
        padding: 1;
    }

    #mapping-body {
        height: 1fr;
    }

    #wav-list-container {
        width: 1fr;
        border: tall #2a3044;
    }

    #assignment-pane {
        width: 30;
        padding: 0 1;
        background: #14161c;
        border-left: tall #2a3044;
    }

    .pad-slot {
        padding: 1 0;
        border-bottom: thin #2a3044;
    }

    .pad-name {
        color: #ffb86c;
        text-style: bold;
    }

    .assigned-file {
        color: #e6e6e6;
        italic: True;
        overflow: ellipsis;
    }
    
    .instruction {
        color: #888;
        italic: True;
        text-align: center;
        padding: 1;
    }
    """

    BINDINGS: ClassVar = [
        ("q", "assign('PAD1')", "Asignar PAD1"),
        ("w", "assign('PAD2')", "Asignar PAD2"),
        ("e", "assign('PAD3')", "Asignar PAD3"),
        ("a", "assign('PAD4')", "Asignar PAD4"),
        ("s", "assign('PAD5')", "Asignar PAD5"),
        ("d", "assign('PAD6')", "Asignar PAD6"),
        ("z", "assign('PAD7')", "Asignar PAD7"),
        ("x", "assign('PAD8')", "Asignar PAD8"),
        ("c", "assign('PAD9')", "Asignar PAD9"),
        ("escape", "cancel", "Cancelar"),
        ("enter", "save", "Guardar y Salir"),
    ]

    def __init__(self, kit_path: Path) -> None:
        super().__init__()
        self.kit_path = kit_path
        self.mapping: dict[PadId, str] = {pad: "" for pad in PAD_IDS}
        self._load_current_mapping()

    def _load_current_mapping(self) -> None:
        mapping_file = self.kit_path / "remi.json"
        if mapping_file.exists():
            try:
                data = json.loads(mapping_file.read_text())
                for pad_id, filename in data.items():
                    if pad_id in PAD_IDS:
                        self.mapping[pad_id] = filename
            except (json.JSONDecodeError, OSError):
                pass

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(f"MAPEANDO KIT: {self.kit_path.name}", id="modal-title")
            with Horizontal(id="mapping-body"):
                with Vertical(id="wav-list-container"):
                    yield Label("Archivos .wav encontrados:", classes="instruction")
                    yield ListView(id="wav-list")
                with Vertical(id="assignment-pane"):
                    yield Label("ASIGNACIONES", classes="pad-name")
                    for pad_id in PAD_IDS:
                        with Vertical(classes="pad-slot", id=f"slot-{pad_id}"):
                            yield Label(f"Pad {pad_id}", classes="pad-name")
                            yield Label(self.mapping[pad_id] or "(vacío)", classes="assigned-file", id=f"label-{pad_id}")
            yield Label("Usa QWE/ASD/ZXC para asignar el archivo seleccionado. ENTER para guardar.", classes="instruction")
            yield Footer()

    def on_mount(self) -> None:
        wav_list = self.query_one("#wav-list", ListView)
        # Buscar wavs recursivamente o solo en el directorio?
        # Para simplificar, buscamos en el directorio actual.
        wavs = sorted([p.name for p in self.kit_path.glob("*.wav")])
        for wav in wavs:
            wav_list.append(ListItem(Label(wav)))

    def action_assign(self, pad_id: PadId) -> None:
        wav_list = self.query_one("#wav-list", ListView)
        selected_item = wav_list.highlighted_child
        if selected_item:
            # Obtener el label del ListItem
            label = selected_item.query_one(Label).renderable
            if isinstance(label, str):
                filename = label
            else:
                filename = str(label)
            
            self.mapping[pad_id] = filename
            self.query_one(f"#label-{pad_id}", Label).update(filename)
            self.notify(f"{filename} -> Pad {pad_id}", timeout=1)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        self.dismiss(self.mapping)
