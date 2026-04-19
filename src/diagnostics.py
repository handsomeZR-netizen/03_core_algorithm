"""Rule-based circuit diagnostics for teaching-oriented feedback."""

from __future__ import annotations

from collections import Counter, defaultdict, deque

from .mna_solver import AMMETER_RESISTANCE, CLOSED_RESISTANCE, OPEN_RESISTANCE, VOLTMETER_RESISTANCE
from .models import CircuitComponent, CircuitModel, DiagnosticItem, SolverResult


SHORT_RISK_RESISTANCE = 1.0e-3
CONDUCTIVE_PATH_RESISTANCE = 1.0e6


def _effective_resistance(component: CircuitComponent) -> float | None:
    """Return the effective branch resistance used for graph-based diagnosis."""
    try:
        if component.type == "resistor":
            return float(component.params["resistance"])
        if component.type == "switch":
            if component.params.get("state", "open") == "closed":
                return float(component.params.get("closed_resistance", CLOSED_RESISTANCE))
            return float(component.params.get("open_resistance", OPEN_RESISTANCE))
        if component.type == "ammeter":
            return float(component.params.get("internal_resistance", AMMETER_RESISTANCE))
        if component.type == "voltmeter":
            return float(component.params.get("internal_resistance", VOLTMETER_RESISTANCE))
    except (KeyError, TypeError, ValueError):
        return None

    return None


def _node_degree_counter(circuit: CircuitModel) -> Counter[str]:
    """Count how many terminals land on each node."""
    counter: Counter[str] = Counter()
    for component in circuit.components:
        counter.update(component.nodes)
    return counter


def _source_terminals(circuit: CircuitModel) -> list[tuple[CircuitComponent, str, str]]:
    """List all independent source terminal pairs."""
    return [
        (component, component.nodes[0], component.nodes[1])
        for component in circuit.components
        if component.type == "voltage_source"
    ]


def _uses_same_node_pair(
    pair_map: dict[tuple[str, str], list[CircuitComponent]],
    component: CircuitComponent,
    excluded_types: set[str],
) -> list[str]:
    """Return component ids that share the exact same terminal pair."""
    pair_key = tuple(sorted(component.nodes))
    return [
        item.id
        for item in pair_map[pair_key]
        if item.id != component.id and item.type not in excluded_types
    ]


def _deduplicate_diagnostics(items: list[DiagnosticItem]) -> list[DiagnosticItem]:
    """Remove duplicated diagnostics while preserving the original order."""
    seen: set[tuple[str, tuple[str, ...]]] = set()
    unique_items: list[DiagnosticItem] = []
    for item in items:
        key = (item.code, tuple(sorted(item.component_ids)))
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)
    return unique_items


def _build_graph(circuit: CircuitModel, threshold: float) -> dict[str, set[str]]:
    """Build an undirected node graph using branches below the given threshold."""
    graph: dict[str, set[str]] = defaultdict(set)
    for component in circuit.components:
        resistance = _effective_resistance(component)
        if resistance is None or resistance > threshold:
            continue
        node_a, node_b = component.nodes
        graph[node_a].add(node_b)
        graph[node_b].add(node_a)
    return graph


def _has_path(graph: dict[str, set[str]], start: str, end: str) -> bool:
    """Check whether two nodes are connected in a simple undirected graph."""
    if start == end:
        return True
    if start not in graph or end not in graph:
        return False

    queue = deque([start])
    visited = {start}
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, set()):
            if neighbor == end:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False


def _component_pair_map(circuit: CircuitModel) -> dict[tuple[str, str], list[CircuitComponent]]:
    """Group components by unordered endpoint pairs."""
    pair_map: dict[tuple[str, str], list[CircuitComponent]] = defaultdict(list)
    for component in circuit.components:
        key = tuple(sorted(component.nodes))
        pair_map[key].append(component)
    return pair_map


def analyze_circuit(
    circuit: CircuitModel,
    solver_result: SolverResult | None,
    validation_issues: list[DiagnosticItem],
) -> list[DiagnosticItem]:
    """Generate rule-based diagnostic messages for wiring and teaching issues."""
    diagnostics: list[DiagnosticItem] = list(validation_issues)
    conductive_graph = _build_graph(circuit, CONDUCTIVE_PATH_RESISTANCE)
    short_graph = _build_graph(circuit, SHORT_RISK_RESISTANCE)
    pair_map = _component_pair_map(circuit)
    degree_counter = _node_degree_counter(circuit)

    for source, positive, negative in _source_terminals(circuit):
        if _has_path(short_graph, positive, negative):
            diagnostics.append(
                DiagnosticItem(
                    severity="error",
                    code="SHORT_RISK",
                    title="短路风险",
                    message=f"电源 {source.id} 的两端存在近似零电阻连通路径，存在短路风险。",
                    component_ids=[source.id],
                    suggestion="移除直接跨接电源的低阻路径，确保电流先经过负载。",
                )
            )
        elif not _has_path(conductive_graph, positive, negative):
            diagnostics.append(
                DiagnosticItem(
                    severity="warning",
                    code="OPEN_CIRCUIT",
                    title="开路",
                    message=f"电源 {source.id} 的正负端没有形成有效闭合回路。",
                    component_ids=[source.id],
                    suggestion="检查开关状态、连线方向，以及是否存在回到电源负极的路径。",
                )
            )

    if solver_result is not None and not solver_result.solved:
        diagnostics.append(
            DiagnosticItem(
                severity="warning",
                code="SOLVER_NOT_CONVERGED",
                title="求解失败",
                message="矩阵求解失败，通常意味着开路、悬空节点或结构不完整。",
                suggestion="优先检查是否存在悬空节点、断开的开关，或电源没有参考回路。",
            )
        )

    for component in circuit.components:
        if component.type == "ammeter":
            parallel_targets = _uses_same_node_pair(pair_map, component, {"voltmeter"})
            if parallel_targets:
                diagnostics.append(
                    DiagnosticItem(
                        severity="warning",
                        code="AMMETER_PARALLEL",
                        title="电流表接法异常",
                        message=f"电流表 {component.id} 与其他元件共用同一对节点，表现为并联接入。",
                        component_ids=[component.id, *parallel_targets],
                        suggestion="电流表应串联在待测支路中，而不是并联跨接在元件两端。",
                    )
                )

        if component.type == "voltmeter":
            parallel_targets = _uses_same_node_pair(pair_map, component, {"ammeter"})
            if not parallel_targets and all(degree_counter[node] <= 2 for node in component.nodes):
                diagnostics.append(
                    DiagnosticItem(
                        severity="warning",
                        code="VOLTMETER_SERIES",
                        title="电压表接法异常",
                        message=f"电压表 {component.id} 没有并联在被测元件两端，更像是串联插入主回路。",
                        component_ids=[component.id],
                        suggestion="电压表应并联连接在被测元件两端，而不是作为主通路的一部分。",
                    )
                )

    for node, degree in degree_counter.items():
        if node == circuit.ground:
            continue
        if degree == 1:
            attached = [
                component.id
                for component in circuit.components
                if node in component.nodes
            ]
            diagnostics.append(
                DiagnosticItem(
                    severity="info",
                    code="FLOATING_NODE",
                    title="悬空节点",
                    message=f"节点 {node} 仅连接到一个元件端点，可能是悬空节点。",
                    component_ids=attached,
                    suggestion="确认该节点是否应继续接回电路主回路，避免只有单端连接。",
                )
            )

    return _deduplicate_diagnostics(diagnostics)
