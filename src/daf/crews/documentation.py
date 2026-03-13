"""Documentation Crew — Phase 4a.

Wires Agents 21–25 into a sequential pipeline exposing a single ``.kickoff()``.
"""
from __future__ import annotations

from daf.crews._stub import StubCrew
from daf.agents.doc_generation import run_doc_generation
from daf.agents.token_catalog import run_token_catalog
from daf.agents.generation_narrative import run_generation_narrative
from daf.agents.decision_record import run_decision_records
from daf.agents.search_index import run_search_index


def create_documentation_crew(output_dir: str) -> StubCrew:
    """Create the Documentation Crew for the given output directory.

    The returned crew's ``.kickoff()`` runs agents 21–25 in sequence:
    1. Doc Generation (Agent 21)
    2. Token Catalog (Agent 22)
    3. Generation Narrative (Agent 23)
    4. Decision Records (Agent 24)
    5. Search Index (Agent 25)

    Args:
        output_dir: Root pipeline output directory (all input and output
            paths are resolved relative to this directory).

    Returns:
        A :class:`~daf.crews._stub.StubCrew` instance ready to ``.kickoff()``.
    """

    def _run() -> None:
        run_doc_generation(output_dir)
        run_token_catalog(output_dir)
        run_generation_narrative(output_dir)
        run_decision_records(output_dir)
        run_search_index(output_dir)

    return StubCrew(name="documentation", run_fn=_run)
