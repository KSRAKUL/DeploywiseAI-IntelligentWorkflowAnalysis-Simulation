"""
Analysis Service — Deploywise AI
Orchestrates the full analysis pipeline:
1. Build graph from validated workflow
2. Run deterministic rules
3. Compute score + verdict
4. Run AI agents (advisory, never affects score)
5. Return complete AnalysisResult
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agents.reviewers import build_agents
from app.config import settings
from app.core.graph import WorkflowGraph, build_graph
from app.core.policy import get_default_policy
from app.core.schemas import (
    AnalysisResult,
    AnalysisStatus,
    Finding,
    Verdict,
    WorkflowInput,
)
from app.core.scoring import compute_score, run_all_rules
from app.llm.fake import FakeLLM
from app.llm.gemini import GeminiLLM
from app.llm.ollama import OllamaLLM
from app.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


def _get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider."""
    if settings.llm_provider == "ollama":
        return OllamaLLM()
    if settings.llm_provider == "gemini":
        return GeminiLLM()
    return FakeLLM()


async def analyze_workflow(
    workflow: WorkflowInput,
    workflow_id: str,
    workflow_version_id: str,
    run_agents: bool = True,
    llm: LLMProvider | None = None,
) -> AnalysisResult:
    """
    Run the full deterministic analysis pipeline.

    The golden rule: deterministic rules decide score/verdict.
    Agents add advisory context only.
    """
    policy = get_default_policy()

    # Phase 1: Build graph
    graph = build_graph(workflow)

    # Phase 2: Run deterministic rules
    rule_findings = run_all_rules(graph, policy)

    # Phase 3: Compute score + verdict (deterministic only)
    analysis = compute_score(
        findings=rule_findings,
        workflow_id=workflow_id,
        workflow_version_id=workflow_version_id,
        policy=policy,
    )

    # Phase 4: Run agents (advisory only, cannot affect score)
    agent_findings: list[Finding] = []
    agent_run_ids: list[str] = []

    if run_agents:
        provider = llm or _get_llm_provider()
        agents = build_agents(provider)
        valid_stage_ids = {s.id for s in workflow.stages}
        workflow_dict = workflow.model_dump(mode="json")

        # Run all agents concurrently
        agent_tasks = [
            agent.run(workflow_dict, rule_findings, valid_stage_ids)
            for agent in agents
        ]
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent task failed with exception: {result}")
                continue
            agent_findings.extend(result.findings)
            agent_run_ids.append(result.role)

    # Merge: rule findings + advisory agent findings
    all_findings = rule_findings + agent_findings

    # Return updated analysis with agent findings (score unchanged)
    from datetime import datetime

    return AnalysisResult(
        analysis_id=analysis.analysis_id,
        workflow_id=workflow_id,
        workflow_version_id=workflow_version_id,
        policy_version=analysis.policy_version,
        rule_set_version=analysis.rule_set_version,
        status=AnalysisStatus.COMPLETE,
        score=analysis.score,  # UNCHANGED by agents
        verdict=analysis.verdict,  # UNCHANGED by agents
        is_blocked=analysis.is_blocked,  # UNCHANGED by agents
        category_scores=analysis.category_scores,  # UNCHANGED by agents
        findings=all_findings,
        agent_run_ids=agent_run_ids,
        created_at=analysis.created_at,
        completed_at=datetime.utcnow(),
    )


async def simulate_what_if(
    original_workflow: WorkflowInput,
    operations: list[dict[str, Any]],
    original_analysis: AnalysisResult,
    workflow_id: str,
    workflow_version_id: str,
) -> dict[str, Any]:
    """
    Apply operations to an in-memory copy and return diff.
    NEVER mutates the original workflow.
    """
    # Apply operations to in-memory copy
    workflow_dict = original_workflow.model_dump(mode="json")
    graph_errors: list[str] = []

    try:
        proposed_dict = _apply_operations(workflow_dict, operations)
        proposed_workflow = WorkflowInput(**proposed_dict)
        proposed_graph = build_graph(proposed_workflow)

        if not proposed_graph.is_valid():
            graph_errors = [e.message for e in proposed_graph.errors]

        # Analyze proposed (no agents for speed)
        proposed_analysis = await analyze_workflow(
            workflow=proposed_workflow,
            workflow_id=workflow_id,
            workflow_version_id=f"{workflow_version_id}-whatif",
            run_agents=False,
        )
    except Exception as e:
        import uuid
        graph_errors.append(str(e))
        return {
            "simulation_id": str(uuid.uuid4()),
            "graph_valid": False,
            "graph_errors": graph_errors,
            "error": str(e),
            "original_analysis": original_analysis.model_dump(mode="json"),
            "proposed_analysis": original_analysis.model_dump(mode="json"),
            "score_delta": 0,
            "verdict_change": False,
            "resolved_findings": [],
            "still_present_findings": [f.finding_id for f in original_analysis.findings if not f.advisory],
            "new_findings": [],
            "original_diagram": None,
            "proposed_diagram": None,
        }

    # Compute diff
    original_finding_ids = {f.finding_id for f in original_analysis.findings if not f.advisory}
    proposed_finding_ids = {f.finding_id for f in proposed_analysis.findings if not f.advisory}

    # Map by rule_id+stage_ids for semantic comparison
    orig_keys = {
        f"{f.rule_id}:{':'.join(sorted(f.stage_ids))}"
        for f in original_analysis.findings
        if not f.advisory
    }
    prop_keys = {
        f"{f.rule_id}:{':'.join(sorted(f.stage_ids))}"
        for f in proposed_analysis.findings
        if not f.advisory
    }

    resolved = [
        f.finding_id for f in original_analysis.findings
        if not f.advisory
        and f"{f.rule_id}:{':'.join(sorted(f.stage_ids))}" not in prop_keys
    ]
    still_present = [
        f.finding_id for f in original_analysis.findings
        if not f.advisory
        and f"{f.rule_id}:{':'.join(sorted(f.stage_ids))}" in prop_keys
    ]
    new_findings = [
        f.finding_id for f in proposed_analysis.findings
        if not f.advisory
        and f"{f.rule_id}:{':'.join(sorted(f.stage_ids))}" not in orig_keys
    ]

    import uuid
    from app.services.diagram_generator import WorkflowDiagramGenerator
    orig_diag = WorkflowDiagramGenerator.generate_existing_diagram(
        original_workflow,
        original_analysis.findings,
        title="Existing Delivery Pipeline"
    )
    orig_stage_ids = {s.id for s in original_workflow.stages}
    prop_diag = WorkflowDiagramGenerator.generate_existing_diagram(
        proposed_workflow,
        proposed_analysis.findings,
        title="Future Delivery Pipeline",
        highlight_new_nodes_from=orig_stage_ids,
    )

    orig_assurance = getattr(original_analysis, "assurance_score", max(0, 100 - original_analysis.score))
    prop_assurance = getattr(proposed_analysis, "assurance_score", max(0, 100 - proposed_analysis.score))

    return {
        "simulation_id": str(uuid.uuid4()),
        "original_analysis": original_analysis.model_dump(mode="json"),
        "proposed_analysis": proposed_analysis.model_dump(mode="json"),
        "score_delta": proposed_analysis.score - original_analysis.score,
        "assurance_score_delta": prop_assurance - orig_assurance,
        "verdict_change": proposed_analysis.verdict != original_analysis.verdict,
        "resolved_findings": resolved,
        "still_present_findings": still_present,
        "new_findings": new_findings,
        "graph_valid": proposed_graph.is_valid(),
        "graph_errors": graph_errors,
        "original_diagram": orig_diag.model_dump(mode="json"),
        "proposed_diagram": prop_diag.model_dump(mode="json"),
    }


def _apply_operations(workflow_dict: dict, operations: list[dict]) -> dict:
    """Apply what-if operations to a workflow dict copy."""
    import copy
    result = copy.deepcopy(workflow_dict)
    stages = {s["id"]: s for s in result.get("stages", [])}
    stage_list = result.get("stages", [])

    for op in operations:
        operation = op.get("operation")

        if operation == "add_stage":
            stage = op.get("stage", {})
            if stage and stage.get("id") not in stages:
                stage_list.append(stage)
                stages[stage["id"]] = stage

        elif operation == "remove_stage":
            sid = op.get("stage_id")
            stage_list = [s for s in stage_list if s["id"] != sid]
            stages.pop(sid, None)
            # Remove references
            for s in stage_list:
                s["depends_on"] = [d for d in s.get("depends_on", []) if d != sid]

        elif operation == "add_dependency":
            from_id = op.get("from_id")
            to_id = op.get("to_id")
            if to_id in stages and from_id not in stages[to_id].get("depends_on", []):
                stages[to_id].setdefault("depends_on", []).append(from_id)

        elif operation == "remove_dependency":
            from_id = op.get("from_id")
            to_id = op.get("to_id")
            if to_id in stages:
                stages[to_id]["depends_on"] = [
                    d for d in stages[to_id].get("depends_on", []) if d != from_id
                ]

        elif operation == "update_stage":
            sid = op.get("stage_id")
            updates = op.get("updates", {})
            if sid in stages:
                stages[sid].update(updates)

    result["stages"] = stage_list
    return result
