"""Rich-powered showcase renderer for the demo mode."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.text import Text

from .models import CircuitModel, DemoPresentation, DemoScenario, DiagnosticItem, SolverResult, TeachingFeedback


SHOWCASE_THEME = TerminalTheme(
    background=(248, 250, 252),
    foreground=(15, 23, 42),
    normal=[
        (30, 64, 175),
        (15, 118, 110),
        (5, 150, 105),
        (181, 83, 9),
        (148, 163, 184),
        (51, 65, 85),
        (8, 145, 178),
        (30, 41, 59),
    ],
    bright=[
        (59, 130, 246),
        (20, 184, 166),
        (34, 197, 94),
        (245, 158, 11),
        (203, 213, 225),
        (71, 85, 105),
        (14, 165, 233),
        (15, 23, 42),
    ],
)

CARD_STYLES = {
    "good": ("#0f766e", "#ecfdf5"),
    "warning": ("#b45309", "#fffbeb"),
    "critical": ("#b91c1c", "#fef2f2"),
    "info": ("#1d4ed8", "#eff6ff"),
}


def create_demo_console(width: int = 112, record: bool = True) -> Console:
    """Create a Rich console configured for showcase rendering."""
    return Console(record=record, width=width, soft_wrap=False)


def render_demo_report(
    console: Console,
    scenario: DemoScenario,
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
    presentation: DemoPresentation,
    compact: bool = False,
) -> None:
    """Render the showcase report into the provided Rich console."""
    console.print(_hero_panel(scenario, presentation), justify="center")
    console.print()
    console.print(_summary_cards(presentation.summary_cards, compact=compact))
    console.print()
    console.print(_metadata_panel(presentation))
    console.print()
    console.print(_results_row(circuit, solver_result, compact=compact))
    console.print()
    console.print(_analysis_row(diagnostics, feedback, presentation, compact=compact))
    console.print()
    console.print(_narrative_panel(presentation))
    console.print()
    console.print(
        Align.center(
            Text(
                "GMAT showcase mode: from circuit state reasoning to instructional action.",
                style="italic #0f766e",
            )
        )
    )


def save_demo_exports(
    console: Console,
    svg_path: str | Path | None = None,
    html_path: str | Path | None = None,
) -> None:
    """Persist the current recorded Rich rendering as SVG and/or HTML."""
    if svg_path:
        svg_target = Path(svg_path)
        svg_target.parent.mkdir(parents=True, exist_ok=True)
        console.save_svg(
            str(svg_target),
            title="03_core_algorithm demo",
            theme=SHOWCASE_THEME,
            clear=False,
        )

    if html_path:
        html_target = Path(html_path)
        html_target.parent.mkdir(parents=True, exist_ok=True)
        console.save_html(str(html_target), theme=SHOWCASE_THEME, clear=False)


def save_demo_png(
    console: Console,
    png_path: str | Path,
    html_path: str | Path | None = None,
    width: int = 1800,
    height: int = 2200,
) -> None:
    """Render the recorded console output to a PNG screenshot via a headless browser."""
    png_target = Path(png_path)
    png_target.parent.mkdir(parents=True, exist_ok=True)

    browser = _find_headless_browser()
    if browser is None:
        raise RuntimeError(
            "No supported headless browser was found. Install Edge or Chrome to enable PNG export."
        )

    temp_html: Path | None = None
    if html_path is None:
        handle, temp_name = tempfile.mkstemp(suffix=".html")
        os.close(handle)
        temp_html = Path(temp_name)
        save_demo_exports(console, html_path=temp_html)
        html_target = temp_html
    else:
        html_target = Path(html_path)
        if not html_target.exists():
            save_demo_exports(console, html_path=html_target)

    file_uri = html_target.resolve().as_uri()
    command = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={png_target.resolve()}",
        "--allow-file-access-from-files",
        file_uri,
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    if temp_html is not None and temp_html.exists():
        temp_html.unlink()


def build_demo_json(
    payload: dict[str, object],
    json_path: str | Path,
) -> None:
    """Save a machine-readable showcase payload to disk."""
    target = Path(json_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _hero_panel(scenario: DemoScenario, presentation: DemoPresentation) -> Panel:
    """Render the showcase header panel."""
    title = Text("GMAT Electrical Lab Showcase", style="bold #1d4ed8")
    subtitle = Text(presentation.scenario_title, style="bold #0f172a")
    description = Text(presentation.scenario_subtitle, style="#475569")
    meta_line = Text(
        f"{scenario.student_name} - {scenario.student_level} - Objective: {scenario.learning_objective}",
        style="#0f766e",
    )
    body = Group(Align.center(title), Align.center(subtitle), Align.center(description), Align.center(meta_line))
    return Panel(body, border_style="#1d4ed8", box=box.ROUNDED, padding=(1, 3))


def _summary_cards(cards: list, compact: bool) -> Columns:
    """Render summary cards as a responsive columns layout."""
    panels: list[Panel] = []
    for card in cards:
        border_color, bg_color = CARD_STYLES.get(card.tone, CARD_STYLES["info"])
        body = Group(
            Text(card.title, style=f"bold {border_color}"),
            Text(card.value, style=f"bold {border_color}", justify="center"),
            Text(card.detail, style="#334155"),
        )
        panels.append(
            Panel(
                body,
                border_style=border_color,
                box=box.ROUNDED,
                padding=(1, 2),
                style=f"on {bg_color}",
            )
        )
    return Columns(panels, expand=True, equal=not compact)


def _metadata_panel(presentation: DemoPresentation) -> Panel:
    """Render scenario metadata as a compact table."""
    table = Table.grid(expand=True)
    table.add_column(style="bold #1d4ed8", ratio=1)
    table.add_column(style="#0f172a", ratio=2)
    for key, value in presentation.metadata_rows:
        table.add_row(key, value)
    return Panel(table, title="Scenario Metadata", border_style="#94a3b8", box=box.ROUNDED)


def _results_row(circuit: CircuitModel, solver_result: SolverResult | None, compact: bool) -> Columns:
    """Render circuit info and solver tables side by side."""
    components_table = Table(box=box.SIMPLE_HEAVY, expand=True)
    components_table.add_column("ID", style="bold #1d4ed8")
    components_table.add_column("Type", style="#0f172a")
    components_table.add_column("Nodes", style="#475569")
    for component in circuit.components[: (4 if compact else len(circuit.components))]:
        components_table.add_row(component.id, component.type, " -> ".join(component.nodes))

    node_table = Table(box=box.SIMPLE_HEAVY, expand=True)
    node_table.add_column("Node", style="bold #1d4ed8")
    node_table.add_column("Voltage (V)", justify="right", style="#0f172a")
    element_table = Table(box=box.SIMPLE_HEAVY, expand=True)
    element_table.add_column("Element", style="bold #1d4ed8")
    element_table.add_column("I (A)", justify="right")
    element_table.add_column("U (V)", justify="right")

    if solver_result and solver_result.solved:
        for node, voltage in sorted(solver_result.node_voltages.items()):
            node_table.add_row(node, f"{voltage:.4f}")
        max_rows = 4 if compact else 8
        for item in solver_result.element_results[:max_rows]:
            element_table.add_row(item.id, f"{item.current:.4f}", f"{item.voltage_drop:.4f}")
    else:
        node_table.add_row("N/A", "No solved voltages")
        element_table.add_row("N/A", "N/A", "N/A")

    left_panel = Panel(
        Group(
            Text("Circuit Components", style="bold #0f172a"),
            components_table,
        ),
        border_style="#94a3b8",
        box=box.ROUNDED,
    )
    right_panel = Panel(
        Group(
            Text("Physical Reasoning Output", style="bold #0f172a"),
            node_table,
            Text("-" * 34, style="#cbd5e1"),
            element_table,
        ),
        border_style="#94a3b8",
        box=box.ROUNDED,
    )
    return Columns([left_panel, right_panel], expand=True, equal=True)


def _analysis_row(
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
    presentation: DemoPresentation,
    compact: bool,
) -> Columns:
    """Render diagnostics and intervention guidance."""
    diagnostics_group = Group(
        Text("Diagnostic Signals", style="bold #0f172a"),
        *[
            Text(
                _diagnostic_display_text(item),
                style=_diagnostic_style(item.severity),
            )
            for item in diagnostics[: (3 if compact else len(diagnostics))]
        ],
    )
    if not diagnostics:
        diagnostics_group = Group(
            Text("Diagnostic Signals", style="bold #0f172a"),
            Text("No structural issues were triggered in the current circuit.", style="#0f766e"),
        )

    feedback_group = Group(
        Text("Heuristic Hints", style="bold #0f766e"),
        *[Text(f"- {item}", style="#0f172a") for item in presentation.heuristic_hints_display[:2]],
        Text("", style="#0f172a"),
        Text("Direct Fixes", style="bold #0f766e"),
        *[Text(f"- {item}", style="#0f172a") for item in presentation.direct_fixes_display[:2]],
        Text("", style="#0f172a"),
        Text("Teacher Actions", style="bold #0f766e"),
        *[Text(f"- {item}", style="#0f172a") for item in presentation.teacher_actions_display[:2]],
    )

    left_panel = Panel(diagnostics_group, border_style="#b45309", box=box.ROUNDED)
    right_panel = Panel(feedback_group, border_style="#0f766e", box=box.ROUNDED)
    return Columns([left_panel, right_panel], expand=True, equal=True)


def _narrative_panel(presentation: DemoPresentation) -> Panel:
    """Render judgement, pedagogical interpretation, and live-demo script."""
    body = Group(
        Text("System Judgement", style="bold #1d4ed8"),
        Text(presentation.system_judgement, style="#0f172a"),
        Text("-" * 92, style="#cbd5e1"),
        Text("Pedagogical Interpretation", style="bold #1d4ed8"),
        Text(presentation.pedagogical_interpretation, style="#0f172a"),
        Text("-" * 92, style="#cbd5e1"),
        Text("Presentation Script", style="bold #1d4ed8"),
        *[Text(f"- {line}", style="#334155") for line in presentation.presentation_script],
        Text("-" * 92, style="#cbd5e1"),
        Text("Teacher Note", style="bold #1d4ed8"),
        Text(presentation.teacher_note, style="#0f172a"),
    )
    return Panel(body, border_style="#1d4ed8", box=box.ROUNDED, title="Showcase Interpretation")


def _diagnostic_style(severity: str) -> str:
    """Map severity to text color."""
    if severity == "error":
        return "#b91c1c"
    if severity == "warning":
        return "#b45309"
    if severity == "info":
        return "#1d4ed8"
    return "#0f172a"


def _diagnostic_display_text(item: DiagnosticItem) -> str:
    """Translate core diagnostic messages into English display copy."""
    translations = {
        "SHORT_RISK": "SHORT_RISK - The source terminals are connected by a near-zero-resistance path.",
        "AMMETER_PARALLEL": "AMMETER_PARALLEL - The ammeter is wired in parallel instead of in series.",
        "VOLTMETER_SERIES": "VOLTMETER_SERIES - The voltmeter has been inserted into the main loop.",
        "OPEN_CIRCUIT": "OPEN_CIRCUIT - The source does not see a valid conductive return path.",
        "SOLVER_NOT_CONVERGED": "SOLVER_NOT_CONVERGED - The solver cannot form a stable operating point from the current topology.",
        "FLOATING_NODE": "FLOATING_NODE - At least one node is connected to only one device terminal.",
        "INVALID_RESISTANCE": "INVALID_RESISTANCE - A resistor value is non-physical or missing.",
        "INVALID_VOLTAGE": "INVALID_VOLTAGE - The source voltage is missing or invalid.",
    }
    return translations.get(item.code, f"{item.code} - {item.title}")


def _find_headless_browser() -> Path | None:
    """Return the first available Chromium-based browser path for screenshots."""
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    for browser_name in ("msedge", "chrome"):
        resolved = shutil.which(browser_name)
        if resolved:
            return Path(resolved)
    return None
