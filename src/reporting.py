"""Helpers for human-readable and JSON CLI output."""

from __future__ import annotations

import json

from .models import CircuitModel, DiagnosticItem, SolverResult, TeachingFeedback


def format_cli_report(
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
) -> str:
    """Render the full demo report for the terminal."""
    lines: list[str] = []

    lines.append("=== 电路基本信息 / Circuit Overview ===")
    lines.append(f"名称: {circuit.name}")
    lines.append(f"说明: {circuit.description or '无'}")
    lines.append(f"参考地: {circuit.ground}")
    lines.append("")

    lines.append("=== 元件清单 / Components ===")
    for component in circuit.components:
        lines.append(
            f"- {component.id:<6} {component.type:<15} nodes={component.nodes} params={component.params}"
        )
    lines.append("")

    lines.append("=== 求解结果摘要 / Solver Summary ===")
    if solver_result is None:
        lines.append("状态: solver_skipped")
        lines.append("原因: 静态校验未通过，已跳过数值求解。")
    else:
        lines.append(f"状态: {solver_result.status}")
        lines.append(f"说明: {solver_result.message}")
        lines.append(f"总功率和: {solver_result.total_power:.6f} W")
    lines.append("")

    lines.append("=== 节点电压 / Node Voltages ===")
    if solver_result is not None and solver_result.solved:
        for node, voltage in sorted(solver_result.node_voltages.items()):
            lines.append(f"- {node:<8} {voltage:>12.6f} V")
    else:
        lines.append("- 无可用节点电压结果")
    lines.append("")

    lines.append("=== 元件电流与电压 / Element Measurements ===")
    if solver_result is not None and solver_result.solved:
        for item in solver_result.element_results:
            lines.append(
                f"- {item.id:<6} I={item.current:>12.6f} A  U={item.voltage_drop:>12.6f} V  P={item.power:>12.6f} W"
            )
    else:
        lines.append("- 无可用元件求解结果")
    lines.append("")

    lines.append("=== 错误分析 / Diagnostics ===")
    if diagnostics:
        for item in diagnostics:
            targets = ", ".join(item.component_ids) if item.component_ids else "N/A"
            lines.append(f"- [{item.severity}] {item.code}: {item.title}")
            lines.append(f"  说明: {item.message}")
            lines.append(f"  关联元件: {targets}")
            lines.append(f"  建议: {item.suggestion or '无'}")
    else:
        lines.append("- 未发现结构性错误，电路适合用于基础教学演示。")
    lines.append("")

    lines.append("=== 教学反馈建议 / HACP-style Feedback ===")
    lines.append(f"干预等级: {feedback.overall_level}")
    lines.append("启发式提示:")
    for tip in feedback.heuristic_hints:
        lines.append(f"- {tip}")
    lines.append("直接纠错:")
    for tip in feedback.direct_fixes:
        lines.append(f"- {tip}")
    lines.append("教师介入建议:")
    for tip in feedback.teacher_actions:
        lines.append(f"- {tip}")
    lines.append("")

    lines.append("=== TODO / Scope Note ===")
    lines.append("- TODO: 当前仅支持直流稳态、两端线性器件和基础教学规则。")
    lines.append("- TODO: 暂不支持受控源、交流分析、瞬态分析和复杂桥式网络自动化解释。")
    return "\n".join(lines)


def build_json_report(
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    diagnostics: list[DiagnosticItem],
    feedback: TeachingFeedback,
) -> str:
    """Render the full report as JSON for tests or downstream integration."""
    payload = {
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
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
