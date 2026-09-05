"""Approval dependency graph + critical-path analysis.

Builds a directed graph of a project's approvals using the ``dependencies``
declared on approval rules, then computes the critical path (longest
duration path) so the UI can highlight what drives overall project time.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Approval, ApprovalRule


class ApprovalGraphService:
    """Compute the approval dependency graph and its critical path."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_graph(self, project_id: UUID) -> dict:
        """Return nodes + edges + critical path for a project's approvals."""
        approvals = await self._get_approvals(project_id)
        rules = await self._get_rules()

        # Map each approval's rule dependencies via rule id (string) and name.
        id_map: dict[str, ApprovalRule] = {str(r.id): r for r in rules}
        name_map: dict[str, ApprovalRule] = {r.name: r for r in rules}
        rule_name_by_key: dict[str, str] = {str(r.id): r.name for r in rules}

        nodes = []
        edge_index = 0
        edges = []
        name_to_node: dict[str, str] = {}  # approval rule name -> node id

        for a in approvals:
            rule = name_map.get(a.name) or id_map.get(str(a.id))
            deps = self._deps_for(rule)
            node_id = str(a.id)
            name_to_node[a.name] = node_id
            nodes.append({
                "id": node_id,
                "label": a.name,
                "department": a.department,
                "days": a.estimated_processing_days or (rule.estimated_processing_days if rule else 0) or 0,
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "dependencies": deps,
            })

        # Resolve each dependency key to an approval node id.
        for n in nodes:
            for dep in n["dependencies"]:
                target_name = rule_name_by_key.get(dep, dep)
                if target_name in name_to_node:
                    edges.append({
                        "id": f"e{edge_index}",
                        "source": name_to_node[target_name],
                        "target": n["id"],
                    })
                    edge_index += 1

        critical_path = await self._critical_path(nodes, edges)
        return {
            "project_id": str(project_id),
            "nodes": nodes,
            "edges": edges,
            "critical_path": critical_path,
        }

    async def _get_approvals(self, project_id: UUID) -> list[Approval]:
        result = await self.db.execute(select(Approval).where(Approval.project_id == project_id))
        return list(result.scalars().all())

    async def _get_rules(self) -> list[ApprovalRule]:
        result = await self.db.execute(select(ApprovalRule))
        return list(result.scalars().all())

    def _deps_for(self, rule: ApprovalRule | None) -> list[str]:
        if not rule:
            return []
        deps = rule.dependencies or []
        if isinstance(deps, str):
            return [deps]
        return list(deps)

    async def _critical_path(self, nodes: list[dict], edges: list[dict]) -> dict:
        """Longest-duration path via longest-path on a DAG using edge (predecessor) days."""
        node_days = {n["id"]: n["days"] for n in nodes}
        # adjacency: parent -> children
        children: dict[str, list[str]] = {n["id"]: [] for n in nodes}
        indegree: dict[str, int] = {n["id"]: 0 for n in nodes}
        for e in edges:
            children.setdefault(e["source"], []).append(e["target"])
            indegree[e["target"]] = indegree.get(e["target"], 0) + 1

        # Earliest start (EST) via DAG topological order; duration includes node's own days.
        queue = [nid for nid, d in indegree.items() if d == 0]
        est = {nid: node_days.get(nid, 0) for nid in queue}
        pred: dict[str, str | None] = {n["id"]: None for n in nodes}
        topo_order = []
        while queue:
            cur = queue.pop(0)
            topo_order.append(cur)
            for child in children.get(cur, []):
                # child's start must wait for cur to finish (est[cur] already includes cur's days)
                candidate = est[cur] + node_days.get(child, 0)
                if candidate > est.get(child, 0):
                    est[child] = candidate
                    pred[child] = cur
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        # Overall duration = max EST (each includes the node's own days).
        duration = max(est.values()) if est else 0
        # Reconstruct critical path from the node achieving the max EST, walking preds.
        end = max(est, key=lambda k: est[k]) if est else None
        path_ids = []
        cur = end
        while cur is not None:
            path_ids.append(cur)
            cur = pred.get(cur)
        path_ids.reverse()

        by_id = {n["id"]: n for n in nodes}
        path_nodes = [by_id.get(pid) for pid in path_ids if pid in by_id]
        return {
            "duration_days": duration,
            "approval_ids": path_ids,
            "approvals": [{"id": n["id"], "name": n["label"], "days": n["days"], "status": n["status"]} for n in path_nodes],
        }