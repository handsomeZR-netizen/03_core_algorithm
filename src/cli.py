"""CLI entry point for the minimal circuit teaching demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .diagnostics import analyze_circuit
from .intervention import build_teaching_feedback
from .mna_solver import solve_dc_circuit
from .parser import load_circuit_from_file
from .reporting import build_json_report, format_cli_report
from .validators import validate_circuit


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Minimal MNA-based circuit teaching demo")
    parser.add_argument("--input", required=True, help="Path to the circuit JSON file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return exit code 1 when any error-level diagnostic appears.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI workflow from file loading to teaching feedback."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    circuit = load_circuit_from_file(input_path)
    validation_issues = validate_circuit(circuit)

    blocking_errors = any(issue.severity == "error" for issue in validation_issues)
    solver_result = None if blocking_errors else solve_dc_circuit(circuit)
    diagnostics = analyze_circuit(circuit, solver_result, validation_issues)
    feedback = build_teaching_feedback(diagnostics)

    if args.json:
        print(build_json_report(circuit, solver_result, diagnostics, feedback))
    else:
        print(format_cli_report(circuit, solver_result, diagnostics, feedback))

    if args.fail_on_error and any(item.severity == "error" for item in diagnostics):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
