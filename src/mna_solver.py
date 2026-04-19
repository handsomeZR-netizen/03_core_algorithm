"""Minimal MNA-based DC solver for two-terminal teaching circuits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import CircuitComponent, CircuitModel, ElementSolution, SolverResult


OPEN_RESISTANCE = 1.0e12
CLOSED_RESISTANCE = 1.0e-6
AMMETER_RESISTANCE = 1.0e-6
VOLTMETER_RESISTANCE = 1.0e12


@dataclass(slots=True)
class BranchStamp:
    """Stores effective branch resistance used by the resistor-style stampler."""

    component: CircuitComponent
    resistance: float
    note: str


def _node_index_map(circuit: CircuitModel) -> dict[str, int]:
    """Build an index map for all non-ground nodes."""
    nodes = sorted(
        {
            node
            for component in circuit.components
            for node in component.nodes
            if node != circuit.ground
        }
    )
    return {node: index for index, node in enumerate(nodes)}


def _effective_branch(component: CircuitComponent) -> BranchStamp | None:
    """Return the equivalent resistance for passive two-terminal branches."""
    if component.type == "resistor":
        return BranchStamp(component=component, resistance=float(component.params["resistance"]), note="resistor")

    if component.type == "switch":
        state = component.params.get("state", "open")
        if state == "closed":
            resistance = float(component.params.get("closed_resistance", CLOSED_RESISTANCE))
            return BranchStamp(component=component, resistance=resistance, note="closed_switch")
        resistance = float(component.params.get("open_resistance", OPEN_RESISTANCE))
        return BranchStamp(component=component, resistance=resistance, note="open_switch")

    if component.type == "ammeter":
        resistance = float(component.params.get("internal_resistance", AMMETER_RESISTANCE))
        return BranchStamp(component=component, resistance=resistance, note="idealized_ammeter")

    if component.type == "voltmeter":
        resistance = float(component.params.get("internal_resistance", VOLTMETER_RESISTANCE))
        return BranchStamp(component=component, resistance=resistance, note="idealized_voltmeter")

    return None


def _stamp_conductance(
    matrix: np.ndarray,
    node_map: dict[str, int],
    ground_node: str,
    positive: str,
    negative: str,
    conductance: float,
) -> None:
    """Apply one resistor-like branch to the MNA conductance matrix."""
    if positive != ground_node:
        i = node_map[positive]
        matrix[i, i] += conductance
    if negative != ground_node:
        j = node_map[negative]
        matrix[j, j] += conductance
    if positive != ground_node and negative != ground_node:
        i = node_map[positive]
        j = node_map[negative]
        matrix[i, j] -= conductance
        matrix[j, i] -= conductance


def solve_dc_circuit(circuit: CircuitModel) -> SolverResult:
    """Solve the circuit using a minimal Modified Nodal Analysis formulation."""
    node_map = _node_index_map(circuit)
    voltage_sources = [component for component in circuit.components if component.type == "voltage_source"]

    node_count = len(node_map)
    source_count = len(voltage_sources)
    matrix_size = node_count + source_count

    if matrix_size == 0:
        return SolverResult(
            solved=False,
            status="skipped",
            message="No solvable variables were found in the circuit.",
        )

    matrix = np.zeros((matrix_size, matrix_size), dtype=float)
    rhs = np.zeros(matrix_size, dtype=float)
    branch_stamps: list[BranchStamp] = []

    for component in circuit.components:
        branch = _effective_branch(component)
        if branch is None:
            continue
        branch_stamps.append(branch)
        conductance = 1.0 / branch.resistance
        _stamp_conductance(
            matrix,
            node_map,
            circuit.ground,
            component.nodes[0],
            component.nodes[1],
            conductance,
        )

    for source_index, source in enumerate(voltage_sources):
        matrix_row = node_count + source_index
        positive, negative = source.nodes
        voltage = float(source.params["voltage"])

        if positive != circuit.ground:
            i = node_map[positive]
            matrix[i, matrix_row] += 1.0
            matrix[matrix_row, i] += 1.0
        if negative != circuit.ground:
            j = node_map[negative]
            matrix[j, matrix_row] -= 1.0
            matrix[matrix_row, j] -= 1.0

        rhs[matrix_row] = voltage

    try:
        solution_vector = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return SolverResult(
            solved=False,
            status="singular",
            message="MNA matrix is singular. The circuit is likely open, floating, or ill-posed.",
            metadata={
                "node_map": node_map,
                "voltage_source_ids": [source.id for source in voltage_sources],
            },
        )

    node_voltages = {circuit.ground: 0.0}
    for node, index in node_map.items():
        node_voltages[node] = float(solution_vector[index])

    source_currents: dict[str, float] = {}
    for source_index, source in enumerate(voltage_sources):
        source_currents[source.id] = float(solution_vector[node_count + source_index])

    element_results: list[ElementSolution] = []
    total_power = 0.0

    for component in circuit.components:
        positive, negative = component.nodes
        voltage_drop = node_voltages.get(positive, 0.0) - node_voltages.get(negative, 0.0)
        current = 0.0
        extra: dict[str, object] = {}

        branch = _effective_branch(component)
        if branch is not None:
            current = voltage_drop / branch.resistance
            extra["effective_resistance"] = branch.resistance
            extra["model"] = branch.note
            power = voltage_drop * current
        elif component.type == "voltage_source":
            current = source_currents[component.id]
            extra["voltage"] = float(component.params["voltage"])
            extra["model"] = "independent_voltage_source"
            power = voltage_drop * current
        else:
            power = 0.0
            extra["model"] = "unsupported_branch"

        total_power += power
        element_results.append(
            ElementSolution(
                id=component.id,
                type=component.type,
                name=component.name,
                nodes=component.nodes,
                current=float(current),
                voltage_drop=float(voltage_drop),
                power=float(power),
                extra=extra,
            )
        )

    return SolverResult(
        solved=True,
        status="solved",
        message="DC operating point solved successfully.",
        node_voltages=node_voltages,
        element_results=element_results,
        total_power=float(total_power),
        metadata={
            "node_map": node_map,
            "voltage_source_currents": source_currents,
            "todo": [
                "TODO: 仅支持直流稳态两端器件网络。",
                "TODO: 暂不支持受控源、交流分析、瞬态分析。",
            ],
        },
    )
