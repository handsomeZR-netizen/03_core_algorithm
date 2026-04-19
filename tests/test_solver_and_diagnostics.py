"""Tests for the minimal circuit demo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.diagnostics import analyze_circuit
from src.intervention import build_teaching_feedback
from src.mna_solver import solve_dc_circuit
from src.parser import load_circuit_from_file, parse_circuit_data
from src.validators import validate_circuit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def _diagnostic_codes(example_name: str) -> set[str]:
    """Load one example and return the triggered diagnostic codes."""
    circuit = load_circuit_from_file(EXAMPLES_DIR / example_name)
    validation = validate_circuit(circuit)
    solver_result = None if any(item.severity == "error" for item in validation) else solve_dc_circuit(circuit)
    diagnostics = analyze_circuit(circuit, solver_result, validation)
    return {item.code for item in diagnostics}


def test_series_circuit_solves_with_expected_current() -> None:
    """Series demo should solve to 0.12 A with a 12 V / 100 ohm load."""
    circuit = load_circuit_from_file(EXAMPLES_DIR / "series_ok.json")
    validation = validate_circuit(circuit)
    assert validation == []

    result = solve_dc_circuit(circuit)
    assert result.solved is True
    assert result.node_voltages["n1"] == pytest.approx(12.0, rel=1e-6)
    assert result.node_voltages["n2"] == pytest.approx(11.99999988, rel=1e-6)

    element_map = {item.id: item for item in result.element_results}
    assert element_map["R1"].current == pytest.approx(0.12, rel=1e-6)


def test_parallel_circuit_branch_currents_match_expected_split() -> None:
    """Parallel demo should produce two branch currents with equal node voltage."""
    circuit = load_circuit_from_file(EXAMPLES_DIR / "parallel_ok.json")
    result = solve_dc_circuit(circuit)
    element_map = {item.id: item for item in result.element_results}

    assert result.solved is True
    assert result.node_voltages["n1"] == pytest.approx(12.0, rel=1e-6)
    assert element_map["R1"].current == pytest.approx(0.12, rel=1e-6)
    assert element_map["R2"].current == pytest.approx(0.06, rel=1e-6)


def test_open_switch_example_reports_open_circuit() -> None:
    """Open switch demo should trigger open-circuit diagnosis."""
    codes = _diagnostic_codes("open_switch.json")
    assert "OPEN_CIRCUIT" in codes


def test_short_risk_example_reports_short_risk() -> None:
    """Short-risk example should trigger the short circuit warning."""
    codes = _diagnostic_codes("short_risk.json")
    assert "SHORT_RISK" in codes


def test_ammeter_parallel_example_reports_meter_error() -> None:
    """Ammeter misuse should be reported as a parallel connection problem."""
    codes = _diagnostic_codes("ammeter_parallel_error.json")
    assert "AMMETER_PARALLEL" in codes


def test_voltmeter_series_example_reports_meter_error() -> None:
    """Voltmeter misuse should be reported as a series connection problem."""
    codes = _diagnostic_codes("voltmeter_series_error.json")
    assert "VOLTMETER_SERIES" in codes


def test_invalid_resistance_is_blocking_validation_error() -> None:
    """Negative resistance should fail validation before the solver runs."""
    circuit = parse_circuit_data(
        {
            "name": "invalid",
            "ground": "gnd",
            "components": [
                {
                    "id": "V1",
                    "type": "voltage_source",
                    "name": "电源",
                    "nodes": ["n1", "gnd"],
                    "params": {"voltage": 5.0},
                },
                {
                    "id": "R1",
                    "type": "resistor",
                    "name": "负载",
                    "nodes": ["n1", "gnd"],
                    "params": {"resistance": -10.0},
                },
            ],
        }
    )
    validation = validate_circuit(circuit)
    assert any(item.code == "INVALID_RESISTANCE" for item in validation)


def test_teaching_feedback_escalates_on_errors() -> None:
    """Error-level diagnostics should produce high-level intervention output."""
    circuit = load_circuit_from_file(EXAMPLES_DIR / "short_risk.json")
    validation = validate_circuit(circuit)
    result = solve_dc_circuit(circuit)
    diagnostics = analyze_circuit(circuit, result, validation)
    feedback = build_teaching_feedback(diagnostics)
    assert feedback.overall_level == "high"
    assert any("短路" in action for action in feedback.teacher_actions)


def test_cli_smoke_output_contains_expected_sections() -> None:
    """CLI should print the key report sections for a valid example."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "--input",
            str(EXAMPLES_DIR / "series_ok.json"),
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout
    assert "电路基本信息" in stdout
    assert "节点电压" in stdout
    assert "教学反馈建议" in stdout


def test_json_examples_can_be_loaded_round_trip() -> None:
    """Every bundled example should be loadable and JSON-complete."""
    for path in EXAMPLES_DIR.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        circuit = parse_circuit_data(raw)
        assert circuit.name
        assert len(circuit.components) >= 1
