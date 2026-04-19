"""Circuit JSON parser for the minimal demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CircuitComponent, CircuitModel


def parse_circuit_data(data: dict[str, Any]) -> CircuitModel:
    """Convert raw JSON data into the internal circuit model."""
    name = str(data.get("name", "Unnamed Circuit"))
    description = str(data.get("description", ""))
    ground = str(data.get("ground", "gnd"))

    components: list[CircuitComponent] = []
    raw_components = data.get("components", [])

    if not isinstance(raw_components, list):
        raise ValueError("Field 'components' must be a list.")

    for index, item in enumerate(raw_components):
        if not isinstance(item, dict):
            raise ValueError(f"Component at index {index} must be an object.")

        component = CircuitComponent(
            id=str(item.get("id", f"component_{index}")),
            type=str(item.get("type", "")),
            name=str(item.get("name", item.get("type", f"component_{index}"))),
            nodes=[str(node) for node in item.get("nodes", [])],
            params=dict(item.get("params", {})),
        )
        components.append(component)

    return CircuitModel(
        name=name,
        description=description,
        ground=ground,
        components=components,
    )


def load_circuit_from_file(path: str | Path) -> CircuitModel:
    """Load a circuit definition from a JSON file."""
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_circuit_data(data)
