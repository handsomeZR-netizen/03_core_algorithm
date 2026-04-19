"""Static validation rules for the minimal circuit format."""

from __future__ import annotations

from .models import CircuitModel, DiagnosticItem, SUPPORTED_COMPONENT_TYPES


def _is_number(value: object) -> bool:
    """Return True when a value can be safely interpreted as a float."""
    return isinstance(value, int | float) and not isinstance(value, bool)


def validate_circuit(circuit: CircuitModel) -> list[DiagnosticItem]:
    """Validate structure and parameter correctness before solving."""
    issues: list[DiagnosticItem] = []
    seen_ids: set[str] = set()

    if not circuit.components:
        issues.append(
            DiagnosticItem(
                severity="error",
                code="EMPTY_CIRCUIT",
                title="电路为空",
                message="电路 JSON 中没有任何元件，无法构成可求解网络。",
                suggestion="至少加入一个电源和一个负载元件。",
            )
        )
        return issues

    for component in circuit.components:
        if component.id in seen_ids:
            issues.append(
                DiagnosticItem(
                    severity="error",
                    code="DUPLICATE_COMPONENT_ID",
                    title="元件 ID 重复",
                    message=f"元件 {component.id} 重复定义，后续结果会产生歧义。",
                    component_ids=[component.id],
                    suggestion="为每个元件分配唯一 ID。",
                )
            )
        seen_ids.add(component.id)

        if component.type not in SUPPORTED_COMPONENT_TYPES:
            issues.append(
                DiagnosticItem(
                    severity="error",
                    code="UNSUPPORTED_COMPONENT_TYPE",
                    title="元件类型不支持",
                    message=f"元件 {component.id} 使用了未支持的类型 {component.type}。",
                    component_ids=[component.id],
                    suggestion="当前 demo 只支持 voltage_source、resistor、switch、ammeter、voltmeter。",
                )
            )

        if len(component.nodes) != 2:
            issues.append(
                DiagnosticItem(
                    severity="error",
                    code="INVALID_NODE_COUNT",
                    title="端点数量异常",
                    message=f"元件 {component.id} 需要恰好两个节点，但当前为 {len(component.nodes)} 个。",
                    component_ids=[component.id],
                    suggestion="请检查 nodes 字段，确保是两个端点节点。",
                )
            )

        if component.type == "resistor":
            resistance = component.params.get("resistance")
            if not _is_number(resistance) or float(resistance) <= 0:
                issues.append(
                    DiagnosticItem(
                        severity="error",
                        code="INVALID_RESISTANCE",
                        title="电阻参数异常",
                        message=f"元件 {component.id} 的 resistance 必须为大于 0 的数字。",
                        component_ids=[component.id],
                        suggestion="将 resistance 设置为正数，例如 100.0。",
                    )
                )

        if component.type == "voltage_source":
            voltage = component.params.get("voltage")
            if not _is_number(voltage):
                issues.append(
                    DiagnosticItem(
                        severity="error",
                        code="INVALID_VOLTAGE",
                        title="电源参数异常",
                        message=f"元件 {component.id} 的 voltage 必须为数字。",
                        component_ids=[component.id],
                        suggestion="将 voltage 设置为数字，例如 6.0 或 12.0。",
                    )
                )

        if component.type == "switch":
            state = component.params.get("state")
            if state not in {"open", "closed"}:
                issues.append(
                    DiagnosticItem(
                        severity="error",
                        code="INVALID_SWITCH_STATE",
                        title="开关状态异常",
                        message=f"元件 {component.id} 的 state 只能是 'open' 或 'closed'。",
                        component_ids=[component.id],
                        suggestion="将 state 修改为 open 或 closed。",
                    )
                )

        if component.type in {"ammeter", "voltmeter"}:
            internal_resistance = component.params.get("internal_resistance")
            if internal_resistance is not None and (
                not _is_number(internal_resistance) or float(internal_resistance) <= 0
            ):
                issues.append(
                    DiagnosticItem(
                        severity="error",
                        code="INVALID_METER_RESISTANCE",
                        title="仪表内阻参数异常",
                        message=f"元件 {component.id} 的 internal_resistance 必须为正数。",
                        component_ids=[component.id],
                        suggestion="将 internal_resistance 设为正数，或删除该字段使用默认值。",
                    )
                )

    source_count = sum(1 for component in circuit.components if component.type == "voltage_source")
    if source_count == 0:
        issues.append(
            DiagnosticItem(
                severity="error",
                code="MISSING_SOURCE",
                title="缺少电源",
                message="当前电路没有 voltage_source，无法进行直流供电求解。",
                suggestion="至少放置一个独立电压源。",
            )
        )

    return issues
