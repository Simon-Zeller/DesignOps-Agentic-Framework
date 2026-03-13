"""State Machine Validator — validates state/transition graphs for reachability.

Detects:
- Terminal states that have outgoing transitions (impossible paths)
- Unreachable states (no incoming edges from any other state)
"""
from __future__ import annotations

from typing import Any


def validate_state_machine(states: dict[str, Any]) -> dict[str, Any]:
    """Validate a spec state machine defined as a dict of state_name → state_config.

    Each state_config may have:
    - ``transitions``: list of target state names (outgoing)
    - ``terminal``: bool (default False) — if True, outgoing transitions are invalid

    Returns:
        ``{
            "valid": bool,
            "invalid_transitions": [{"from": ..., "to": ..., "reason": ...}, ...],
            "unreachable_states": [...],
        }``
    """
    invalid_transitions: list[dict[str, str]] = []
    unreachable_states: list[str] = []

    if not states:
        return {"valid": True, "invalid_transitions": [], "unreachable_states": []}

    # Build incoming edge map
    incoming: dict[str, list[str]] = {s: [] for s in states}

    for state_name, config in states.items():
        if not isinstance(config, dict):
            continue
        is_terminal = config.get("terminal", False)
        transitions = config.get("transitions", [])

        for target in transitions:
            if is_terminal:
                invalid_transitions.append({
                    "from": state_name,
                    "to": target,
                    "reason": "terminal state cannot have outgoing transitions",
                })
            if target in incoming:
                incoming[target].append(state_name)

    # Find unreachable states: states with no incoming edges (excluding the first/initial state)
    state_names = list(states.keys())
    initial_state = state_names[0] if state_names else None

    for state_name in state_names:
        if state_name == initial_state:
            continue
        if not incoming.get(state_name):
            unreachable_states.append(state_name)

    is_valid = len(invalid_transitions) == 0

    return {
        "valid": is_valid,
        "invalid_transitions": invalid_transitions,
        "unreachable_states": unreachable_states,
    }
