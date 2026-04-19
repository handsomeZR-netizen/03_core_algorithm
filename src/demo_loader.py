"""Load curated showcase scenarios for the display-focused demo mode."""

from __future__ import annotations

import json
from pathlib import Path

from .models import CircuitModel, DemoScenario
from .parser import load_circuit_from_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def list_demo_scenarios() -> list[DemoScenario]:
    """Return all curated showcase scenarios sorted by filename."""
    scenarios: list[DemoScenario] = []
    for path in sorted(DEMO_DATA_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        scenarios.append(DemoScenario(**payload))
    return scenarios


def load_demo_scenario(name: str) -> tuple[DemoScenario, CircuitModel]:
    """Load one named showcase scenario and its linked circuit example."""
    path = DEMO_DATA_DIR / f"{name}.json"
    if not path.exists():
        available = ", ".join(scenario.id for scenario in list_demo_scenarios())
        raise FileNotFoundError(
            f"Unknown demo scenario '{name}'. Available scenarios: {available}"
        )

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    scenario = DemoScenario(**payload)
    circuit_path = EXAMPLES_DIR / scenario.example_file
    circuit = load_circuit_from_file(circuit_path)
    return scenario, circuit


def build_ad_hoc_demo_scenario(example_path: str | Path, circuit: CircuitModel) -> DemoScenario:
    """Create a generic showcase scenario for demo mode when no preset is used."""
    return DemoScenario(
        id="custom_demo",
        title=f"Custom Showcase · {circuit.name}",
        subtitle="Ad-hoc demonstration generated from a user-provided circuit file.",
        example_file=str(Path(example_path).name),
        student_name="Showcase Student",
        student_level="Introductory Lab",
        lab_task=circuit.description or "Interpret the current circuit state and explain the result.",
        attempt_index=1,
        elapsed_seconds=180,
        error_count=0,
        engagement_score=82,
        confidence_score=76,
        learning_objective="Connect physical reasoning with explainable tutoring feedback.",
        presentation_summary="This custom scenario is rendered through the same solver, diagnostic, and intervention stack as the curated showcase set.",
        teacher_note="Use the exported report to walk through how the system turns a raw circuit into a teaching-oriented explanation.",
        force_teacher_handoff=False,
    )
