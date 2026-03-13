"""Priority Queue Builder — converts a classified, dependency-ordered component list into a priority queue."""
from __future__ import annotations

_TIER_ORDER = {"primitive": 0, "simple": 1, "complex": 2}


def build_priority_queue(
    classified_components: list[dict],
    topo_order: list[str],
) -> list[dict]:
    """Return classified components sorted primitive → simple → complex.

    Within each tier, components are ordered by their position in *topo_order*
    so that dependencies are always generated before dependents.

    Args:
        classified_components: List of dicts with ``name`` and ``tier`` keys.
        topo_order: Topological order from :func:`dependency_graph_builder.topological_sort`.

    Returns:
        Sorted list of component dicts.
    """
    topo_index = {name: i for i, name in enumerate(topo_order)}

    def _sort_key(item: dict) -> tuple[int, int]:
        tier_rank = _TIER_ORDER.get(item.get("tier", "simple"), 1)
        position = topo_index.get(item.get("name", ""), len(topo_order))
        return (tier_rank, position)

    return sorted(classified_components, key=_sort_key)
