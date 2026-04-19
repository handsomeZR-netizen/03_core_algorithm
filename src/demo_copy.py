"""Transform solver outputs into showcase-ready demo copy."""

from __future__ import annotations

from .models import (
    CircuitModel,
    DemoPresentation,
    DemoScenario,
    DemoSummaryCard,
    DiagnosticItem,
    SolverResult,
    TeachingFeedback,
)


def build_demo_presentation(
    scenario: DemoScenario,
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
) -> DemoPresentation:
    """Build presentation-oriented copy and summary cards for the showcase UI."""
    severity = _highest_severity(diagnostics)
    codes = {item.code for item in diagnostics}

    state_value = _circuit_state_label(solver_result, codes)
    risk_value = _risk_label(severity, codes)
    intervention_value = _intervention_label(scenario, feedback)
    solver_value = "Solved" if solver_result and solver_result.solved else "Blocked"

    summary_cards = [
        DemoSummaryCard(
            title="Circuit State",
            value=state_value,
            detail=scenario.presentation_summary,
            tone=_state_tone(severity, codes),
        ),
        DemoSummaryCard(
            title="Solver Status",
            value=solver_value,
            detail=(solver_result.message if solver_result else "Static validation blocked numerical solving."),
            tone="good" if solver_result and solver_result.solved else "warning",
        ),
        DemoSummaryCard(
            title="Risk Level",
            value=risk_value,
            detail=_risk_detail(diagnostics),
            tone=_state_tone(severity, codes),
        ),
        DemoSummaryCard(
            title="Intervention",
            value=intervention_value,
            detail=_intervention_detail(scenario, feedback),
            tone="critical" if intervention_value == "Teacher Handoff" else "info",
        ),
    ]

    system_judgement = _system_judgement(state_value, diagnostics, solver_result)
    pedagogical_interpretation = _pedagogical_interpretation(scenario, codes, solver_result)
    recommended_next_step = _recommended_next_step(scenario, codes, feedback)
    presentation_script = _presentation_script(
        scenario=scenario,
        state_value=state_value,
        risk_value=risk_value,
        recommended_next_step=recommended_next_step,
    )

    metadata_rows = [
        ("Student", scenario.student_name),
        ("Level", scenario.student_level),
        ("Task", scenario.lab_task),
        ("Attempt", f"No. {scenario.attempt_index}"),
        ("Elapsed", f"{scenario.elapsed_seconds}s"),
        ("Errors", str(scenario.error_count)),
        ("Engagement", f"{scenario.engagement_score}/100"),
        ("Confidence", f"{scenario.confidence_score}/100"),
        ("Objective", scenario.learning_objective),
    ]
    heuristic_hints_display, direct_fixes_display, teacher_actions_display = _feedback_display_copy(
        scenario,
        codes,
        feedback,
    )

    return DemoPresentation(
        scenario_title=scenario.title,
        scenario_subtitle=scenario.subtitle,
        summary_cards=summary_cards,
        system_judgement=system_judgement,
        pedagogical_interpretation=pedagogical_interpretation,
        recommended_next_step=recommended_next_step,
        presentation_script=presentation_script,
        teacher_note=scenario.teacher_note,
        metadata_rows=metadata_rows,
        heuristic_hints_display=heuristic_hints_display,
        direct_fixes_display=direct_fixes_display,
        teacher_actions_display=teacher_actions_display,
    )


def build_demo_payload(
    scenario: DemoScenario,
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
    presentation: DemoPresentation,
) -> dict[str, object]:
    """Build a machine-readable export payload for the showcase mode."""
    return {
        "scenario": scenario.to_dict(),
        "circuit": {
            "name": circuit.name,
            "description": circuit.description,
            "ground": circuit.ground,
            "components": [
                {
                    "id": component.id,
                    "type": component.type,
                    "name": component.name,
                    "nodes": component.nodes,
                    "params": component.params,
                }
                for component in circuit.components
            ],
        },
        "solver_result": None if solver_result is None else solver_result.to_dict(),
        "diagnostics": [item.to_dict() for item in diagnostics],
        "teaching_feedback": feedback.to_dict(),
        "presentation": presentation.to_dict(),
    }


def _highest_severity(diagnostics: list[DiagnosticItem]) -> str:
    """Return the highest diagnostic severity across the current scenario."""
    if any(item.severity == "error" for item in diagnostics):
        return "error"
    if any(item.severity == "warning" for item in diagnostics):
        return "warning"
    if any(item.severity == "info" for item in diagnostics):
        return "info"
    return "none"


def _circuit_state_label(solver_result: SolverResult | None, codes: set[str]) -> str:
    """Map current diagnostic codes to a concise state label."""
    if "SHORT_RISK" in codes:
        return "Unsafe Wiring"
    if "AMMETER_PARALLEL" in codes or "VOLTMETER_SERIES" in codes:
        return "Instrument Miswire"
    if "OPEN_CIRCUIT" in codes:
        return "Open Circuit"
    if solver_result and solver_result.solved:
        return "Closed Loop"
    return "Underspecified"


def _risk_label(severity: str, codes: set[str]) -> str:
    """Map diagnostics to a concise risk label."""
    if "SHORT_RISK" in codes:
        return "Critical"
    if severity == "error":
        return "High"
    if severity == "warning":
        return "Elevated"
    if severity == "info":
        return "Low"
    return "Stable"


def _intervention_label(scenario: DemoScenario, feedback: TeachingFeedback) -> str:
    """Map intervention state to a display-friendly label."""
    if scenario.force_teacher_handoff or scenario.error_count >= 4 or feedback.overall_level == "high":
        return "Teacher Handoff"
    if feedback.overall_level in {"medium", "light"}:
        return "Guided Correction"
    return "Reflective Coaching"


def _risk_detail(diagnostics: list[DiagnosticItem]) -> str:
    """Build a short detail string for the risk summary card."""
    if not diagnostics:
        return "No structural warnings were triggered in the current circuit."
    top_items = [f"{item.code} ({item.severity})" for item in diagnostics[:2]]
    return " | ".join(top_items)


def _intervention_detail(scenario: DemoScenario, feedback: TeachingFeedback) -> str:
    """Build a short detail string for the intervention summary card."""
    if scenario.force_teacher_handoff:
        return "Escalation is forced by repeated unsuccessful attempts in the showcase metadata."
    if feedback.overall_level == "high":
        return "The current state requires immediate instructor attention."
    if feedback.overall_level in {"medium", "light"}:
        return "The system can still guide the learner through one focused correction cycle."
    return "The system can continue with reflective feedback."


def _state_tone(severity: str, codes: set[str]) -> str:
    """Choose the visual tone for state and risk cards."""
    if "SHORT_RISK" in codes or severity == "error":
        return "critical"
    if severity == "warning":
        return "warning"
    if severity == "info":
        return "info"
    return "good"


def _system_judgement(
    state_value: str,
    diagnostics: list[DiagnosticItem],
    solver_result: SolverResult | None,
) -> str:
    """Generate a concise system-level judgement sentence."""
    codes = {item.code for item in diagnostics}
    if "SHORT_RISK" in codes:
        return "The wiring creates a near-zero-resistance path across the source and must be treated as unsafe before any instructional discussion continues."
    if "AMMETER_PARALLEL" in codes:
        return "The circuit is electrically solvable, but the measurement strategy is invalid because the ammeter is bypassing the intended branch logic."
    if "VOLTMETER_SERIES" in codes:
        return "The measurement chain behaves like an artificial open path because the voltmeter has been inserted into the main loop instead of across the target load."
    if "OPEN_CIRCUIT" in codes:
        return "The source terminals are not connected by a valid conductive path, so the circuit does not form a usable closed loop."
    if solver_result and solver_result.solved:
        return f"The current circuit is structurally valid and the solver returns a stable DC operating point labeled as '{state_value}'."
    return "The circuit could not be resolved into a stable operating condition, so the system should stay in diagnostic-first mode."


def _pedagogical_interpretation(
    scenario: DemoScenario,
    codes: set[str],
    solver_result: SolverResult | None,
) -> str:
    """Generate an instructional interpretation of the current state."""
    if "SHORT_RISK" in codes:
        return "This is not merely a wrong answer; it is a safety-sensitive state. The instructional priority shifts from conceptual coaching to immediate risk containment and supervised correction."
    if "AMMETER_PARALLEL" in codes:
        return "The learner is confusing current measurement with voltage observation. The system should use this moment to reinforce why current must be measured through the branch rather than across the load."
    if "VOLTMETER_SERIES" in codes:
        return "The learner has attached a high-impedance instrument as though it were part of the conductive path. This creates a strong opportunity to explain why voltmeters reveal potential difference rather than carry the main loop current."
    if "OPEN_CIRCUIT" in codes:
        return "The solver evidence can be translated into a simple teaching narrative: no closed return path means no sustained current, regardless of the nominal source voltage."
    if solver_result and solver_result.solved:
        return f"The scenario now supports a more conceptual discussion around {scenario.learning_objective.lower()} instead of basic troubleshooting."
    return "The system should stay in troubleshooting mode until the circuit regains a meaningful physical interpretation."


def _recommended_next_step(
    scenario: DemoScenario,
    codes: set[str],
    feedback: TeachingFeedback,
) -> str:
    """Generate a concise next-step recommendation."""
    if scenario.force_teacher_handoff or scenario.error_count >= 4:
        return "Pause autonomous guidance, bring the instructor into the loop, and use the current state as a supervised correction case."
    if "SHORT_RISK" in codes:
        return "Stop the trial, isolate the unsafe low-resistance path, and verify the corrected wiring before restarting the exercise."
    if "AMMETER_PARALLEL" in codes:
        return "Move the ammeter into series with the target branch, then re-run the measurement to compare the new reading with the current faulty state."
    if "VOLTMETER_SERIES" in codes:
        return "Relocate the voltmeter across the load, then ask the learner to predict how the current path changes."
    if "OPEN_CIRCUIT" in codes:
        return "Restore a closed return path before discussing any numerical readings or higher-level physics interpretation."
    if feedback.overall_level in {"medium", "light"}:
        return "Apply one focused wiring correction, then ask the learner to explain what changed in the current path."
    return "Continue with conceptual coaching and ask the learner to explain the observed node voltages in their own words."


def _presentation_script(
    scenario: DemoScenario,
    state_value: str,
    risk_value: str,
    recommended_next_step: str,
) -> list[str]:
    """Generate a short presentation script for live demos."""
    return [
        f"{scenario.student_name} is currently working on '{scenario.lab_task}' in scenario '{scenario.title}'.",
        f"The system classifies the circuit state as {state_value} with risk level {risk_value.lower()} after attempt {scenario.attempt_index}.",
        recommended_next_step,
    ]


def _feedback_display_copy(
    scenario: DemoScenario,
    codes: set[str],
    feedback: TeachingFeedback,
) -> tuple[list[str], list[str], list[str]]:
    """Build English display copy for the showcase feedback panel."""
    heuristic_hints: list[str] = []
    direct_fixes: list[str] = []
    teacher_actions: list[str] = []

    if "SHORT_RISK" in codes:
        heuristic_hints.append("The source terminals are effectively bridged by a very low-resistance path.")
        direct_fixes.append("Break the shortcut path before restarting the circuit.")
        teacher_actions.append("Switch from autonomous coaching to supervised correction immediately.")
    if "AMMETER_PARALLEL" in codes:
        heuristic_hints.append("The ammeter is bypassing the intended branch rather than measuring through it.")
        direct_fixes.append("Insert the ammeter in series with the target branch.")
        teacher_actions.append("Ask the learner to compare series and parallel measurement logic side by side.")
    if "VOLTMETER_SERIES" in codes:
        heuristic_hints.append("The voltmeter is sitting inside the main loop instead of across the target element.")
        direct_fixes.append("Reconnect the voltmeter across the load terminals.")
        teacher_actions.append("Use the high-impedance model to explain why the loop current collapses.")
    if "OPEN_CIRCUIT" in codes:
        heuristic_hints.append("No closed return path exists between the source terminals.")
        direct_fixes.append("Restore a complete conductive loop before interpreting any readings.")
        teacher_actions.append("Reconstruct the minimal closed loop on the board before returning control to the learner.")

    if not heuristic_hints:
        heuristic_hints.append("The circuit is structurally stable, so the learner can move from troubleshooting to explanation.")
    if not direct_fixes:
        direct_fixes.append("Use the solved voltages and currents to explain why the current reading matches the load value.")
    if not teacher_actions:
        teacher_actions.append("Keep the instructor in a light-touch coaching role while the learner explains the result.")

    if scenario.force_teacher_handoff or scenario.error_count >= 4 or feedback.overall_level == "high":
        teacher_actions.insert(0, "Escalate to instructor-led correction after repeated or safety-sensitive errors.")

    return _unique_copy(heuristic_hints), _unique_copy(direct_fixes), _unique_copy(teacher_actions)


def _unique_copy(items: list[str]) -> list[str]:
    """Remove duplicated display copy while preserving the original order."""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
