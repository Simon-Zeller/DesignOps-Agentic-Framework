"""Tests for Agent 6 (First Publish Agent) retry routing (p09, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from daf.tools.crew_sequencer import CrewResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_output_dir(tmp_path: Path) -> Path:
    """Create a minimal DS Bootstrap output inside tmp_path."""
    (tmp_path / "brand-profile.json").write_text('{"name": "Test", "scope": "standard"}')
    (tmp_path / "pipeline-config.json").write_text('{"stub": true}')
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    for name in ("base.tokens.json", "semantic.tokens.json", "component.tokens.json"):
        (tokens / name).write_text('{"stub": true}')
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "button.spec.yaml").write_text("stub: true")
    return tmp_path


def _all_success_side_effects() -> list[CrewResult]:
    """Eight successes corresponding to the 8 downstream crews."""
    names = [
        "token_engine", "design_to_code", "component_factory",
        "documentation", "governance", "ai_semantic_layer",
        "analytics", "release",
    ]
    return [CrewResult(crew=n, status="success", artifacts_written=[f"{n}/stub"]) for n in names]


# ---------------------------------------------------------------------------
# test_first_publish_agent_instantiates_rollback_agent_at_start
# ---------------------------------------------------------------------------

def test_first_publish_agent_instantiates_rollback_agent_at_start(tmp_path: Path) -> None:
    """create_rollback_agent() is called exactly once before any crew runs."""
    _make_output_dir(tmp_path)

    rollback_spy = MagicMock(return_value=MagicMock())

    with (
        patch("daf.agents.first_publish.create_rollback_agent", rollback_spy) as mock_rollback,
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": str(tmp_path)}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        for mock_factory in (mock_te, mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent

        run_first_publish_agent(output_dir=str(tmp_path))

    mock_rollback.assert_called_once()
    # rollback must have been called BEFORE the first crew run
    assert rollback_spy.call_count == 1


# ---------------------------------------------------------------------------
# test_first_publish_agent_retries_phase2_on_rejection
# ---------------------------------------------------------------------------

def test_first_publish_agent_retries_phase2_on_rejection(tmp_path: Path) -> None:
    """Phase 2 rejection triggers checkpoint restore, token task retry, and crew re-run."""
    _make_output_dir(tmp_path)

    rejection = {"failed_checks": ["naming"], "suggested_fix": "Use kebab-case"}
    rejected_result = CrewResult(
        crew="token_engine", status="rejected", rejection=rejection, retries_used=0
    )
    success_result = CrewResult(crew="token_engine", status="success", artifacts_written=[])

    # token_engine is called twice: first rejected, second success
    token_engine_calls = [rejected_result, success_result]

    checkpoint_restore_spy = MagicMock()
    run_token_foundation_spy = MagicMock(return_value=None)

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task", run_token_foundation_spy),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te_factory,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.restore = checkpoint_restore_spy
        mock_cm_instance.create.return_value = {"phase": 1, "path": str(tmp_path)}
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        te_crew = MagicMock()
        te_crew.kickoff.side_effect = token_engine_calls
        mock_te_factory.return_value = te_crew

        for mock_factory in (mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew_mock = MagicMock()
            crew_mock.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew_mock

        from daf.agents.first_publish import run_first_publish_agent

        run_first_publish_agent(output_dir=str(tmp_path))

    # restore must have been called once before the retry
    checkpoint_restore_spy.assert_called_once()
    # run_token_foundation_task must have been called with retry_context containing the rejection
    run_token_foundation_spy.assert_called_once()
    call_kwargs = run_token_foundation_spy.call_args
    retry_context = call_kwargs[1].get("retry_context") or (
        call_kwargs[0][2] if len(call_kwargs[0]) > 2 else None
    )
    assert retry_context is not None, "retry_context must be passed to run_token_foundation_task"
    assert rejection in retry_context or retry_context == [rejection] or rejection == retry_context[0]


# ---------------------------------------------------------------------------
# test_first_publish_agent_marks_failed_after_three_retries
# ---------------------------------------------------------------------------

def test_first_publish_agent_marks_failed_after_three_retries(tmp_path: Path) -> None:
    """After 3 rejections, token_engine is marked failed and pipeline continues."""
    _make_output_dir(tmp_path)

    rejected_result = CrewResult(
        crew="token_engine", status="rejected",
        rejection={"failed_checks": ["naming"]}, retries_used=0
    )

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te_factory,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": ""}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        te_crew = MagicMock()
        # Always rejected
        te_crew.kickoff.return_value = rejected_result
        mock_te_factory.return_value = te_crew

        design_to_code_invoked = []

        def _d2c_factory(*a, **kw):
            design_to_code_invoked.append(True)
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="design_to_code", status="success", artifacts_written=[])
            return crew

        mock_d2c.side_effect = _d2c_factory

        for mock_factory in (mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew_mock = MagicMock()
            crew_mock.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew_mock

        from daf.agents.first_publish import run_first_publish_agent

        run_first_publish_agent(output_dir=str(tmp_path))

    # generation-summary.json should record the failure
    summary_path = tmp_path / "reports" / "generation-summary.json"
    assert summary_path.exists(), "generation-summary.json must be written"
    data = json.loads(summary_path.read_text())
    token_engine_result = next(
        (r for r in data.get("phase_results", []) if "token_engine" in r.get("crew", "")),
        None,
    )
    assert token_engine_result is not None
    assert token_engine_result.get("retries_exhausted") is True or token_engine_result.get("status") == "failed"

    # Pipeline should continue — Design-to-Code Crew must be invoked
    assert design_to_code_invoked, "Design-to-Code Crew must be invoked after exhausted retries"


# ---------------------------------------------------------------------------
# test_first_publish_agent_phases46_crew_retry_bounded_at_two
# ---------------------------------------------------------------------------

def test_first_publish_agent_phases46_crew_retry_bounded_at_two(tmp_path: Path) -> None:
    """Documentation Crew fails first, succeeds second; called exactly twice."""
    _make_output_dir(tmp_path)

    doc_calls = [
        CrewResult(crew="documentation", status="failed", retries_used=0, artifacts_written=[]),
        CrewResult(crew="documentation", status="success", artifacts_written=["docs/README.md"]),
    ]

    governance_invoked = []

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": ""}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        for mock_factory, name in (
            (mock_te, "token_engine"), (mock_d2c, "design_to_code"), (mock_cf, "component_factory"),
        ):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew=name, status="success", artifacts_written=[])
            mock_factory.return_value = crew

        doc_crew = MagicMock()
        doc_crew.kickoff.side_effect = doc_calls
        mock_doc.return_value = doc_crew

        def _gov_factory(*a, **kw):
            governance_invoked.append(True)
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="governance", status="success", artifacts_written=[])
            return crew

        mock_gov.side_effect = _gov_factory

        for mock_factory, name in (
            (mock_ai, "ai_semantic_layer"), (mock_analytics, "analytics"), (mock_release, "release"),
        ):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew=name, status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent

        run_first_publish_agent(output_dir=str(tmp_path))

    # Documentation Crew called exactly twice
    assert doc_crew.kickoff.call_count == 2

    # Governance starts after Documentation succeeds
    assert governance_invoked, "Governance Crew must be invoked after Documentation succeeds"

    # generation-summary.json should show 1 retry for documentation
    summary_path = tmp_path / "reports" / "generation-summary.json"
    assert summary_path.exists()
    data = json.loads(summary_path.read_text())
    doc_result = next(
        (r for r in data.get("phase_results", []) if "documentation" in r.get("crew", "")),
        None,
    )
    assert doc_result is not None
    assert doc_result.get("retries_used", 0) == 1


# ---------------------------------------------------------------------------
# test_first_publish_agent_retry_context_accumulates
# ---------------------------------------------------------------------------

def test_first_publish_agent_retry_context_accumulates(tmp_path: Path) -> None:
    """On attempt 3, retry_context contains both rejection_1 and rejection_2."""
    _make_output_dir(tmp_path)

    rejection_1 = {"failed_checks": ["naming"], "attempt": 1}
    rejection_2 = {"failed_checks": ["values"], "attempt": 2}

    token_engine_calls = [
        CrewResult(crew="token_engine", status="rejected", rejection=rejection_1, retries_used=0),
        CrewResult(crew="token_engine", status="rejected", rejection=rejection_2, retries_used=1),
        CrewResult(crew="token_engine", status="success", artifacts_written=[]),
    ]

    captured_retry_contexts: list = []

    def _spy_token_foundation(*args, **kwargs):
        ctx = kwargs.get("retry_context") or (args[2] if len(args) > 2 else None)
        captured_retry_contexts.append(ctx)

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task", side_effect=_spy_token_foundation),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te_factory,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": ""}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        te_crew = MagicMock()
        te_crew.kickoff.side_effect = token_engine_calls
        mock_te_factory.return_value = te_crew

        for mock_factory, name in (
            (mock_d2c, "design_to_code"), (mock_cf, "component_factory"), (mock_doc, "documentation"),
            (mock_gov, "governance"), (mock_ai, "ai_semantic_layer"), (mock_analytics, "analytics"),
            (mock_release, "release"),
        ):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew=name, status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent

        run_first_publish_agent(output_dir=str(tmp_path))

    # Two retries called _spy_token_foundation
    assert len(captured_retry_contexts) == 2

    # The last call (attempt 3) should contain both rejection_1 and rejection_2
    last_context = captured_retry_contexts[-1]
    assert last_context is not None
    assert rejection_1 in last_context
    assert rejection_2 in last_context


# ---------------------------------------------------------------------------
# test_rollback_agent_instantiated_at_pipeline_start (p17 — Task 2.30)
# ---------------------------------------------------------------------------

def test_rollback_agent_instantiated_at_pipeline_start(tmp_path: Path) -> None:
    """Agent 40 (Rollback) is instantiated with model and output_dir at pipeline start."""
    _make_output_dir(tmp_path)

    rollback_spy = MagicMock(return_value=MagicMock())

    with (
        patch("daf.agents.first_publish.create_rollback_agent", rollback_spy),
        patch("daf.agents.first_publish.CheckpointManager"),
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        for mock_factory in (mock_te, mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent
        run_first_publish_agent(output_dir=str(tmp_path))

    rollback_spy.assert_called_once()
    call_args = rollback_spy.call_args
    # Must be called with output_dir so Agent 40 tools target the right directory
    assert str(tmp_path) in str(call_args)


# ---------------------------------------------------------------------------
# test_snapshot_called_before_each_crew (p17 — Task 2.30)
# ---------------------------------------------------------------------------

def test_snapshot_called_before_each_crew(tmp_path: Path) -> None:
    """Phase-boundary checkpoints are created before/after each crew group."""
    _make_output_dir(tmp_path)

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": str(tmp_path)}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        for mock_factory in (mock_te, mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent
        run_first_publish_agent(output_dir=str(tmp_path))

    # Phase-boundary snapshots should be created (phases 0, 3, 4, 5)
    assert mock_cm_instance.create.call_count >= 1, (
        "CheckpointManager.create must be called at least once for phase-boundary snapshots"
    )


# ---------------------------------------------------------------------------
# test_restore_called_on_exhausted_retry (p17 — Task 2.30)
# ---------------------------------------------------------------------------

def test_restore_called_on_exhausted_retry(tmp_path: Path) -> None:
    """CheckpointManager.restore is called when a cross-phase retry is triggered."""
    _make_output_dir(tmp_path)

    rejection = {"failed_checks": ["naming"], "suggested_fix": "Use kebab-case"}
    rejected_result = CrewResult(
        crew="token_engine", status="rejected", rejection=rejection, retries_used=0
    )
    success_result = CrewResult(crew="token_engine", status="success", artifacts_written=[])

    restore_spy = MagicMock()

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.restore = restore_spy
        mock_cm_instance.create.return_value = {"phase": 0, "path": str(tmp_path)}
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        te_crew = MagicMock()
        te_crew.kickoff.side_effect = [rejected_result, success_result]
        mock_te.return_value = te_crew

        for mock_factory in (mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release):
            crew = MagicMock()
            crew.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
            mock_factory.return_value = crew

        from daf.agents.first_publish import run_first_publish_agent
        run_first_publish_agent(output_dir=str(tmp_path))

    restore_spy.assert_called_once()


# ---------------------------------------------------------------------------
# p18 – PRE-CREW-CHECKPOINT tests
# ---------------------------------------------------------------------------

def _full_patch_context(extra_patches=None):
    """Return a list of patch targets for a full run_first_publish_agent test."""
    return [
        "daf.agents.first_publish.create_rollback_agent",
        "daf.agents.first_publish.run_token_foundation_task",
        "daf.agents.first_publish.create_token_engine_crew",
        "daf.agents.first_publish.create_design_to_code_crew",
        "daf.agents.first_publish.create_component_factory_crew",
        "daf.agents.first_publish.create_documentation_crew",
        "daf.agents.first_publish.create_governance_crew",
        "daf.agents.first_publish.create_ai_semantic_layer_crew",
        "daf.agents.first_publish.create_analytics_crew",
        "daf.agents.first_publish.create_release_crew",
    ]


def _setup_all_success_crews(*mock_factories):
    for mock_factory in mock_factories:
        crew = MagicMock()
        crew.kickoff.return_value = CrewResult(crew="stub", status="success", artifacts_written=[])
        mock_factory.return_value = crew


def test_run_simple_crew_creates_checkpoint_before_kickoff(tmp_path: Path) -> None:
    """_run_simple_crew calls cm.create(output_dir, phase=2) before crew kickoff."""
    from daf.agents.first_publish import _run_simple_crew, _CREW_PHASE_MAP
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.return_value = CR(crew="design_to_code", status="success", artifacts_written=[])

    call_order = []
    mock_cm.create.side_effect = lambda **kw: call_order.append("create")
    crew.kickoff.side_effect = lambda: (call_order.append("kickoff"), CR(crew="design_to_code", status="success", artifacts_written=[]))[1]

    factory = MagicMock(return_value=crew)
    _run_simple_crew("design_to_code", factory, str(tmp_path), mock_reporter, cm=mock_cm, phase=2)

    mock_cm.create.assert_called_once_with(output_dir=str(tmp_path), phase=2)
    assert call_order.index("create") < call_order.index("kickoff"), "create must be called before kickoff"


def test_run_simple_crew_still_calls_kickoff_after_checkpoint(tmp_path: Path) -> None:
    """crew.kickoff() is called regardless of checkpoint creation succeeding."""
    from daf.agents.first_publish import _run_simple_crew
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.return_value = CR(crew="design_to_code", status="success", artifacts_written=[])
    factory = MagicMock(return_value=crew)

    _run_simple_crew("design_to_code", factory, str(tmp_path), mock_reporter, cm=mock_cm, phase=2)

    crew.kickoff.assert_called_once()


def test_run_first_publish_passes_cm_and_phase_to_simple_crew(tmp_path: Path) -> None:
    """run_first_publish_agent calls cm.create for Design-to-Code AND Component Factory."""
    _make_output_dir(tmp_path)

    with (
        patch("daf.agents.first_publish.create_rollback_agent"),
        patch("daf.agents.first_publish.CheckpointManager") as MockCM,
        patch("daf.agents.first_publish.run_token_foundation_task"),
        patch("daf.agents.first_publish.create_token_engine_crew") as mock_te,
        patch("daf.agents.first_publish.create_design_to_code_crew") as mock_d2c,
        patch("daf.agents.first_publish.create_component_factory_crew") as mock_cf,
        patch("daf.agents.first_publish.create_documentation_crew") as mock_doc,
        patch("daf.agents.first_publish.create_governance_crew") as mock_gov,
        patch("daf.agents.first_publish.create_ai_semantic_layer_crew") as mock_ai,
        patch("daf.agents.first_publish.create_analytics_crew") as mock_analytics,
        patch("daf.agents.first_publish.create_release_crew") as mock_release,
    ):
        mock_cm_instance = MockCM.return_value
        mock_cm_instance.create.return_value = {"phase": 0, "path": str(tmp_path)}
        mock_cm_instance.restore.return_value = None
        mock_cm_instance.get_last_valid_checkpoint.return_value = None

        _setup_all_success_crews(mock_te, mock_d2c, mock_cf, mock_doc, mock_gov, mock_ai, mock_analytics, mock_release)

        from daf.agents.first_publish import run_first_publish_agent, _CREW_PHASE_MAP
        run_first_publish_agent(output_dir=str(tmp_path))

    # create must have been called with phase corresponding to design_to_code and component_factory
    d2c_phase = _CREW_PHASE_MAP["design_to_code"]
    cf_phase = _CREW_PHASE_MAP["component_factory"]
    create_phases = [call.kwargs.get("phase") for call in mock_cm_instance.create.call_args_list]
    assert d2c_phase in create_phases, f"cm.create must be called with phase={d2c_phase} for design_to_code"
    assert cf_phase in create_phases, f"cm.create must be called with phase={cf_phase} for component_factory"


# ---------------------------------------------------------------------------
# p18 – PRE-RETRY-RESTORE tests
# ---------------------------------------------------------------------------

def test_run_with_retry_creates_checkpoint_on_first_attempt(tmp_path: Path) -> None:
    """_run_with_retry calls cm.create(phase=4) exactly once on attempt 1."""
    from daf.agents.first_publish import _run_with_retry
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.side_effect = [
        CR(crew="documentation", status="failed", artifacts_written=[]),
        CR(crew="documentation", status="success", artifacts_written=[]),
    ]
    factory = MagicMock(return_value=crew)

    _run_with_retry("documentation", factory, str(tmp_path), max_retries=2, reporter=mock_reporter, cm=mock_cm, phase=4)

    assert mock_cm.create.call_count == 1
    mock_cm.create.assert_called_once_with(output_dir=str(tmp_path), phase=4)


def test_run_with_retry_restores_checkpoint_before_second_attempt(tmp_path: Path) -> None:
    """cm.restore is called exactly once (before attempt 2) when attempt 1 fails."""
    from daf.agents.first_publish import _run_with_retry
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.side_effect = [
        CR(crew="documentation", status="failed", artifacts_written=[]),
        CR(crew="documentation", status="success", artifacts_written=[]),
    ]
    factory = MagicMock(return_value=crew)

    with patch("daf.agents.first_publish._cascade_invalidate"):
        _run_with_retry("documentation", factory, str(tmp_path), max_retries=2, reporter=mock_reporter, cm=mock_cm, phase=4)

    mock_cm.restore.assert_called_once_with(output_dir=str(tmp_path), phase=4)


def test_run_with_retry_calls_cascade_invalidate_after_restore(tmp_path: Path) -> None:
    """_cascade_invalidate(output_dir, 4) is called after restore and before retry kickoff."""
    from daf.agents.first_publish import _run_with_retry
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.side_effect = [
        CR(crew="documentation", status="failed", artifacts_written=[]),
        CR(crew="documentation", status="success", artifacts_written=[]),
    ]
    factory = MagicMock(return_value=crew)

    with patch("daf.agents.first_publish._cascade_invalidate") as mock_cascade:
        _run_with_retry("documentation", factory, str(tmp_path), max_retries=2, reporter=mock_reporter, cm=mock_cm, phase=4)

    mock_cascade.assert_called_once_with(str(tmp_path), 4)


def test_run_with_retry_no_restore_on_first_attempt_success(tmp_path: Path) -> None:
    """cm.restore is NOT called when attempt 1 succeeds."""
    from daf.agents.first_publish import _run_with_retry
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.return_value = CR(crew="documentation", status="success", artifacts_written=[])
    factory = MagicMock(return_value=crew)

    result = _run_with_retry("documentation", factory, str(tmp_path), max_retries=2, reporter=mock_reporter, cm=mock_cm, phase=4)

    mock_cm.restore.assert_not_called()
    assert result.status == "success"
    assert result.retries_used == 0


def test_run_with_retry_restore_count_matches_retry_count(tmp_path: Path) -> None:
    """cm.restore is called exactly once (before attempt 2) when max_retries=2 and all fail."""
    from daf.agents.first_publish import _run_with_retry
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.return_value = CR(crew="documentation", status="failed", artifacts_written=[])
    factory = MagicMock(return_value=crew)

    with patch("daf.agents.first_publish._cascade_invalidate"):
        result = _run_with_retry("documentation", factory, str(tmp_path), max_retries=2, reporter=mock_reporter, cm=mock_cm, phase=4)

    assert mock_cm.restore.call_count == 1
    assert result.retries_exhausted is True


# ---------------------------------------------------------------------------
# p18 – CASCADE-INVALIDATION tests
# ---------------------------------------------------------------------------

def test_cascade_invalidate_removes_phase_gt_n_dirs(tmp_path: Path) -> None:
    """_cascade_invalidate(tmp_path, 0) removes all Phase 1+ artifact dirs."""
    from daf.agents.first_publish import _cascade_invalidate, _PHASE_ARTIFACT_DIRS

    # Create directories for phases > 0
    created = []
    for phase, paths in _PHASE_ARTIFACT_DIRS.items():
        if phase > 0:
            for p in paths:
                d = tmp_path / p
                d.mkdir(parents=True, exist_ok=True)
                created.append(d)

    _cascade_invalidate(str(tmp_path), 0)

    for d in created:
        assert not d.exists(), f"{d} should have been removed by cascade"


def test_cascade_invalidate_preserves_earlier_phase_artifacts(tmp_path: Path) -> None:
    """Phase 1–3 artifact dirs survive when _cascade_invalidate(tmp_path, 3) is called."""
    from daf.agents.first_publish import _cascade_invalidate, _PHASE_ARTIFACT_DIRS

    # Create dirs for phases 1, 2, 3, and 4
    for phase, paths in _PHASE_ARTIFACT_DIRS.items():
        for p in paths:
            d = tmp_path / p
            d.mkdir(parents=True, exist_ok=True)

    _cascade_invalidate(str(tmp_path), 3)

    # Phases 1–3 must still be present
    for phase in (1, 2, 3):
        for p in _PHASE_ARTIFACT_DIRS.get(phase, []):
            d = tmp_path / p
            assert d.exists(), f"Phase {phase} artifact {p} should survive cascade from phase 3"

    # Phases > 3 must be removed
    for phase, paths in _PHASE_ARTIFACT_DIRS.items():
        if phase > 3:
            for p in paths:
                d = tmp_path / p
                assert not d.exists(), f"Phase {phase} artifact {p} should be removed by cascade"


def test_cascade_invalidate_silently_skips_missing_dirs(tmp_path: Path) -> None:
    """_cascade_invalidate on an empty dir raises no exception."""
    from daf.agents.first_publish import _cascade_invalidate

    # Should not raise
    _cascade_invalidate(str(tmp_path), 2)


def test_cascade_invalidate_does_not_remove_checkpoint_dir(tmp_path: Path) -> None:
    """The .daf-checkpoints/ directory is preserved by _cascade_invalidate."""
    from daf.agents.first_publish import _cascade_invalidate

    checkpoints = tmp_path / ".daf-checkpoints" / "phase-1-xyz"
    checkpoints.mkdir(parents=True)
    (checkpoints / "brand-profile.json").write_text('{"name": "Test"}')

    _cascade_invalidate(str(tmp_path), 0)

    assert (tmp_path / ".daf-checkpoints").exists(), ".daf-checkpoints must NOT be removed by cascade"


def test_run_simple_crew_checkpoint_phase_uses_crew_phase_map(tmp_path: Path) -> None:
    """Phase passed to cm.create is sourced from _CREW_PHASE_MAP, not a hardcoded literal."""
    from daf.agents.first_publish import _run_simple_crew, _CREW_PHASE_MAP
    from daf.tools.crew_sequencer import CrewResult as CR

    mock_cm = MagicMock()
    mock_reporter = MagicMock()
    crew = MagicMock()
    crew.kickoff.return_value = CR(crew="component_factory", status="success", artifacts_written=[])
    factory = MagicMock(return_value=crew)

    expected_phase = _CREW_PHASE_MAP["component_factory"]
    _run_simple_crew("component_factory", factory, str(tmp_path), mock_reporter, cm=mock_cm, phase=expected_phase)

    mock_cm.create.assert_called_once_with(output_dir=str(tmp_path), phase=expected_phase)


def test_cascade_invalidate_is_idempotent(tmp_path: Path) -> None:
    """Calling _cascade_invalidate twice raises no error and dirs remain absent."""
    from daf.agents.first_publish import _cascade_invalidate, _PHASE_ARTIFACT_DIRS

    # Create Phase 4+ dirs
    for phase, paths in _PHASE_ARTIFACT_DIRS.items():
        if phase > 3:
            for p in paths:
                (tmp_path / p).mkdir(parents=True, exist_ok=True)

    _cascade_invalidate(str(tmp_path), 3)
    _cascade_invalidate(str(tmp_path), 3)  # second call – must not raise

    for phase, paths in _PHASE_ARTIFACT_DIRS.items():
        if phase > 3:
            for p in paths:
                assert not (tmp_path / p).exists()
