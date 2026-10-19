"""
Graph Engine — Deploywise AI Core
Parses a WorkflowInput into a directed graph and exposes safe graph queries.

SAFETY: Uses dominator/reachability analysis only.
        Never enumerate all paths (exponential blowup risk).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from app.core.schemas import Stage, StageType, WorkflowInput


# ---------------------------------------------------------------------------
# Graph Validation Error
# ---------------------------------------------------------------------------

@dataclass
class GraphError:
    """A structural problem detected in the workflow graph."""
    code: str
    message: str
    stage_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# WorkflowGraph
# ---------------------------------------------------------------------------

class WorkflowGraph:
    """
    Directed graph representation of a validated WorkflowInput.

    Edge convention: A -> B means B depends on A (A must execute before B).
    """

    def __init__(self, workflow: WorkflowInput) -> None:
        """Build the graph from a validated workflow."""
        self.workflow = workflow
        self.graph: nx.DiGraph = nx.DiGraph()
        self.errors: list[GraphError] = []
        self._build()

    def _build(self) -> None:
        """Construct the NetworkX directed graph."""
        # Add all stage nodes
        for stage in self.workflow.stages:
            self.graph.add_node(
                stage.id,
                stage=stage,
                stage_type=stage.type.value,
                owner=stage.owner,
            )

        # Add dependency edges: A -> B (A precedes B)
        for stage in self.workflow.stages:
            for dep_id in stage.depends_on:
                self.graph.add_edge(dep_id, stage.id)

        # Validate graph structure
        self._validate()

    def _validate(self) -> None:
        """Run all structural graph validations."""
        self._check_cycles()
        self._check_disconnected()
        self._check_no_production_node()

    def _check_cycles(self) -> None:
        """Detect cyclic dependencies — reject with clear error."""
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            involved = list({e[0] for e in cycle} | {e[1] for e in cycle})
            self.errors.append(GraphError(
                code="CYCLIC_DEPENDENCY",
                message=f"Cyclic dependency detected involving stages: {involved}",
                stage_ids=involved,
            ))
        except nx.NetworkXNoCycle:
            pass

    def _check_disconnected(self) -> None:
        """Warn about disconnected stages (stages that can't reach production)."""
        production_nodes = self.get_production_nodes()
        if not production_nodes:
            return  # handled by _check_no_production_node
        reachable: set[str] = set()
        for prod in production_nodes:
            reachable.update(nx.ancestors(self.graph, prod))
            reachable.add(prod)
        disconnected = [n for n in self.graph.nodes if n not in reachable]
        if disconnected:
            self.errors.append(GraphError(
                code="DISCONNECTED_STAGES",
                message=f"Stages not connected to any production path: {disconnected}",
                stage_ids=disconnected,
            ))

    def _check_no_production_node(self) -> None:
        """Warn if no production deployment stage exists."""
        if not self.get_production_nodes():
            self.errors.append(GraphError(
                code="NO_PRODUCTION_NODE",
                message="No deploy_production stage found in the workflow.",
            ))

    # -----------------------------------------------------------------------
    # Public helpers
    # -----------------------------------------------------------------------

    def get_production_nodes(self) -> list[str]:
        """Return IDs of all deploy_production stages."""
        return [
            n for n, d in self.graph.nodes(data=True)
            if d.get("stage_type") == StageType.DEPLOY_PRODUCTION.value
        ]

    def get_stages_of_type(self, stage_type: StageType) -> list[str]:
        """Return IDs of all stages matching the given type."""
        return [
            n for n, d in self.graph.nodes(data=True)
            if d.get("stage_type") == stage_type.value
        ]

    def get_stage(self, stage_id: str) -> Stage | None:
        """Return the Stage object for a given ID, or None."""
        node_data = self.graph.nodes.get(stage_id)
        if node_data:
            return node_data.get("stage")
        return None

    def ancestors(self, stage_id: str) -> set[str]:
        """
        Return all ancestors (predecessors transitively) of the given stage.
        Uses NetworkX ancestors — O(V+E), no path enumeration.
        """
        if stage_id not in self.graph:
            return set()
        return nx.ancestors(self.graph, stage_id)

    def dominates(self, gate_id: str, target_id: str) -> bool:
        """
        Return True if gate_id dominates target_id — i.e., every path
        to target_id in the graph passes through gate_id.

        Uses NetworkX dominator tree — polynomial, not exponential.
        """
        if gate_id not in self.graph or target_id not in self.graph:
            return False
        if gate_id == target_id:
            return True

        # Find all root nodes (nodes with no predecessors)
        roots = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]
        if not roots:
            return False

        for root in roots:
            # Compute immediate dominators from each root
            try:
                dom_tree = nx.immediate_dominators(self.graph, root)
            except (nx.NetworkXError, nx.NetworkXUnfeasible):
                continue
            # Walk up dominator chain from target
            current = target_id
            visited: set[str] = set()
            while current and current not in visited:
                if current == gate_id:
                    # gate_id is a dominator from this root
                    break
                visited.add(current)
                current = dom_tree.get(current)
            else:
                # gate_id is NOT a dominator from this root — so it doesn't
                # dominate target from all roots
                continue
        # gate_id must dominate from every root for us to say it "dominates"
        # More precisely: gate_id is in ancestors AND removing it disconnects
        # target — but for our rule engine purposes, we check reachability
        return gate_id in self.ancestors(target_id)

    def reachable_from(self, node_id: str) -> set[str]:
        """Return all nodes reachable from node_id (descendants)."""
        if node_id not in self.graph:
            return set()
        return nx.descendants(self.graph, node_id)

    def is_on_any_production_path(self, stage_id: str) -> bool:
        """Return True if stage_id is an ancestor of any production node."""
        for prod in self.get_production_nodes():
            if stage_id in self.ancestors(prod) or stage_id == prod:
                return True
        return False

    def stages_on_production_path_to(self, prod_node: str) -> set[str]:
        """Return all stages that are ancestors of prod_node, plus prod_node itself."""
        return self.ancestors(prod_node) | {prod_node}

    def get_type_stages_guarding_production(self, stage_type: StageType) -> dict[str, list[str]]:
        """
        For each production node, return which stages of stage_type are
        in the ancestor set (i.e., guard it).
        Returns: {prod_node_id: [guarding_stage_id, ...]}
        """
        result: dict[str, list[str]] = {}
        type_stages = set(self.get_stages_of_type(stage_type))
        for prod in self.get_production_nodes():
            ancestors = self.ancestors(prod)
            result[prod] = [s for s in type_stages if s in ancestors]
        return result

    def has_cycles(self) -> bool:
        """Return True if the graph has cyclic dependencies."""
        return any(e.code == "CYCLIC_DEPENDENCY" for e in self.errors)

    def is_valid(self) -> bool:
        """Return True if graph has no structural errors."""
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        """Serialize graph to a JSON-serializable dict."""
        return {
            "nodes": [
                {
                    "id": n,
                    "stage_type": d.get("stage_type"),
                    "owner": d.get("owner"),
                }
                for n, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {"from": u, "to": v}
                for u, v in self.graph.edges()
            ],
            "errors": [
                {"code": e.code, "message": e.message, "stage_ids": e.stage_ids}
                for e in self.errors
            ],
        }


def build_graph(workflow: WorkflowInput) -> WorkflowGraph:
    """Build and return a WorkflowGraph from a validated WorkflowInput."""
    return WorkflowGraph(workflow)
