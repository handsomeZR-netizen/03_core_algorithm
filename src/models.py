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


@dataclass(slots=True)
class DemoScenario:
    """Stores display-oriented metadata for one curated showcase scenario."""

    id: str
    title: str
    subtitle: str
    example_file: str
    student_name: str
    student_level: str
    lab_task: str
    attempt_index: int
    elapsed_seconds: int
    error_count: int
    engagement_score: int
    confidence_score: int
    learning_objective: str
    presentation_summary: str
    teacher_note: str
    force_teacher_handoff: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the showcase scenario metadata."""
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "example_file": self.example_file,
            "student_name": self.student_name,
            "student_level": self.student_level,
            "lab_task": self.lab_task,
            "attempt_index": self.attempt_index,
            "elapsed_seconds": self.elapsed_seconds,
            "error_count": self.error_count,
            "engagement_score": self.engagement_score,
            "confidence_score": self.confidence_score,
            "learning_objective": self.learning_objective,
            "presentation_summary": self.presentation_summary,
            "teacher_note": self.teacher_note,
            "force_teacher_handoff": self.force_teacher_handoff,
        }


@dataclass(slots=True)
class DemoSummaryCard:
    """Stores one high-level summary card for the showcase renderer."""

    title: str
    value: str
    detail: str
    tone: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the summary card for exports."""
        return {
            "title": self.title,
            "value": self.value,
            "detail": self.detail,
            "tone": self.tone,
        }


@dataclass(slots=True)
class DemoPresentation:
    """Stores display-ready copy and metadata for the demo renderer."""

    scenario_title: str
    scenario_subtitle: str
    summary_cards: list[DemoSummaryCard] = field(default_factory=list)
    system_judgement: str = ""
    pedagogical_interpretation: str = ""
    recommended_next_step: str = ""
    presentation_script: list[str] = field(default_factory=list)
    teacher_note: str = ""
    metadata_rows: list[tuple[str, str]] = field(default_factory=list)
    heuristic_hints_display: list[str] = field(default_factory=list)
    direct_fixes_display: list[str] = field(default_factory=list)
    teacher_actions_display: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the presentation copy for machine-readable exports."""
        return {
            "scenario_title": self.scenario_title,
            "scenario_subtitle": self.scenario_subtitle,
            "summary_cards": [card.to_dict() for card in self.summary_cards],
            "system_judgement": self.system_judgement,
            "pedagogical_interpretation": self.pedagogical_interpretation,
            "recommended_next_step": self.recommended_next_step,
            "presentation_script": self.presentation_script,
            "teacher_note": self.teacher_note,
            "metadata_rows": self.metadata_rows,
            "heuristic_hints_display": self.heuristic_hints_display,
            "direct_fixes_display": self.direct_fixes_display,
            "teacher_actions_display": self.teacher_actions_display,
        }
