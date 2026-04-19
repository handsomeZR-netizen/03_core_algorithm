"""CLI entry point for the minimal circuit teaching demo and showcase mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .demo_copy import build_demo_payload, build_demo_presentation
from .demo_loader import build_ad_hoc_demo_scenario, list_demo_scenarios, load_demo_scenario
from .demo_presenter import build_demo_json, create_demo_console, render_demo_report, save_demo_exports, save_demo_png
from .diagnostics import analyze_circuit
from .intervention import build_teaching_feedback
from .mna_solver import solve_dc_circuit
from .parser import load_circuit_from_file
from .reporting import build_json_report, format_cli_report
from .validators import validate_circuit


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Minimal MNA-based circuit teaching demo")
    parser.add_argument("--input", help="Path to the circuit JSON file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return exit code 1 when any error-level diagnostic appears.",
    )
    parser.add_argument("--demo", action="store_true", help="Enable the showcase-oriented demo mode.")
    parser.add_argument("--scenario", help="Curated showcase scenario name used in demo mode.")
    parser.add_argument("--list-scenarios", action="store_true", help="List curated demo scenarios and exit.")
    parser.add_argument("--compact", action="store_true", help="Render a tighter demo layout for single-screen screenshots.")
    parser.add_argument("--export-svg", help="Save the showcase rendering as an SVG file.")
    parser.add_argument("--export-html", help="Save the showcase rendering as an HTML file.")
    parser.add_argument("--export-png", help="Save the showcase rendering as a PNG screenshot.")
    parser.add_argument("--export-json", help="Save the current run as a JSON file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI workflow from file loading to teaching feedback."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        if args.list_scenarios:
            return _list_scenarios()

        if args.demo:
            return _run_demo_mode(args, parser)

        if not args.input:
            parser.error("--input is required unless --demo or --list-scenarios is used.")

        return _run_standard_mode(args)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def _run_standard_mode(args: argparse.Namespace) -> int:
    """Run the original plain-text CLI flow."""
    input_path = Path(args.input)
    circuit = load_circuit_from_file(input_path)
    validation_issues = validate_circuit(circuit)

    blocking_errors = any(issue.severity == "error" for issue in validation_issues)
    solver_result = None if blocking_errors else solve_dc_circuit(circuit)
    diagnostics = analyze_circuit(circuit, solver_result, validation_issues)
    feedback = build_teaching_feedback(diagnostics)

    payload = build_json_report(circuit, solver_result, diagnostics, feedback)
    if args.export_json:
        Path(args.export_json).write_text(payload, encoding="utf-8")

    if args.json:
        print(payload)
    else:
        print(format_cli_report(circuit, solver_result, diagnostics, feedback))

    if args.fail_on_error and any(item.severity == "error" for item in diagnostics):
        return 1
    return 0


def _run_demo_mode(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Run the richer showcase mode with curated scenarios and asset exports."""
    if args.scenario:
        scenario, circuit = load_demo_scenario(args.scenario)
    elif args.input:
        circuit = load_circuit_from_file(Path(args.input))
        scenario = build_ad_hoc_demo_scenario(args.input, circuit)
    else:
        scenario, circuit = load_demo_scenario("normal_lab")

    validation_issues = validate_circuit(circuit)
    blocking_errors = any(issue.severity == "error" for issue in validation_issues)
    solver_result = None if blocking_errors else solve_dc_circuit(circuit)
    diagnostics = analyze_circuit(circuit, solver_result, validation_issues)
    feedback = build_teaching_feedback(diagnostics)
    presentation = build_demo_presentation(scenario, circuit, solver_result, diagnostics, feedback)
    payload = build_demo_payload(scenario, circuit, solver_result, diagnostics, feedback, presentation)

    if args.export_json:
        build_demo_json(payload, args.export_json)

    needs_visual_export = any([args.export_svg, args.export_html, args.export_png]) or not args.json
    console = None
    if needs_visual_export:
        width = 96 if args.compact else 120
        console = create_demo_console(width=width, record=True)
        render_demo_report(
            console=console,
            scenario=scenario,
            circuit=circuit,
            solver_result=solver_result,
            diagnostics=diagnostics,
            feedback=feedback,
            presentation=presentation,
            compact=args.compact,
        )
        save_demo_exports(console, svg_path=args.export_svg, html_path=args.export_html)
        if args.export_png:
            save_demo_png(console, png_path=args.export_png, html_path=args.export_html)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.fail_on_error and any(item.severity == "error" for item in diagnostics):
        return 1
    return 0


def _list_scenarios() -> int:
    """Print the built-in showcase scenario catalog."""
    print("Available demo scenarios:")
    for scenario in list_demo_scenarios():
        print(f"- {scenario.id}: {scenario.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
