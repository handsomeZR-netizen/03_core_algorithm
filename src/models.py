"""Data models for the minimal circuit-solving demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SUPPORTED_COMPONENT_TYPES = {
    "voltage_source",
    "resistor",
    "switch",
    "ammeter",
    "voltmeter",
}


@dataclass(slots=True)
class CircuitComponent:
    """Represents one two-terminal component in the teaching circuit."""

    id: str
    type: str
    name: str
    nodes: list[str]
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CircuitModel:
    """Represents the full circuit parsed from JSON input."""

    name: str
    description: str
    ground: str
    components: list[CircuitComponent]


@dataclass(slots=True)
class DiagnosticItem:
    """Represents a validation or diagnosis message shown to the user."""

    severity: str
    code: str
    title: str
    message: str
    component_ids: list[str] = field(default_factory=list)
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the diagnostic item for CLI JSON output."""
        return {
            "severity": self.severity,
            "code": self.code,
            "title": self.title,
            "message": self.message,
            "component_ids": self.component_ids,
            "suggestion": self.suggestion,
        }


@dataclass(slots=True)
class ElementSolution:
    """Stores solved current, voltage, and power for one element."""

    id: str
    type: str
    name: str
    nodes: list[str]
    current: float
    voltage_drop: float
    power: float
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the element-level result."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "nodes": self.nodes,
            "current": self.current,
            "voltage_drop": self.voltage_drop,
            "power": self.power,
            "extra": self.extra,
        }


@dataclass(slots=True)
class SolverResult:
    """Stores the outcome of the DC MNA solver."""

    solved: bool
    status: str
    message: str
    node_voltages: dict[str, float] = field(default_factory=dict)
    element_results: list[ElementSolution] = field(default_factory=list)
    total_power: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the solver result for machine-readable output."""
        return {
            "solved": self.solved,
            "status": self.status,
            "message": self.message,
            "node_voltages": self.node_voltages,
            "element_results": [item.to_dict() for item in self.element_results],
            "total_power": self.total_power,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class TeachingFeedback:
    """Stores heuristic and corrective teaching interventions."""

    overall_level: str
    heuristic_hints: list[str] = field(default_factory=list)
    direct_fixes: list[str] = field(default_factory=list)
    teacher_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the teaching advice."""
        return {
            "overall_level": self.overall_level,
            "heuristic_hints": self.heuristic_hints,
            "direct_fixes": self.direct_fixes,
            "teacher_actions": self.teacher_actions,
        }
