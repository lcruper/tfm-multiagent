"""
eSHP Planner Module
------------------

Euclidean Shortest Hamiltonian Path (eSHP) solver with fixed start point.

This module implements an optimization-based path planner using Gurobi,
solving a Hamiltonian path problem with lazy subtour elimination constraints.
"""

import gurobipy as gp
from collections import deque
from typing import List, Tuple, Dict

from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner


class eSHPPlanner(IPathPlanner):
    """
    Euclidean Shortest Hamiltonian Path planner.

    This planner computes the minimum-length Hamiltonian path that:
    - starts from a fixed start point
    - visits all remaining points exactly once
    - minimizes the total Euclidean distance

    The problem is solved using Gurobi with lazy subtour elimination.
    """

    # ---------------------------------------------------
    # Internal methods
    # ---------------------------------------------------
    def _find_components(self, n: int, edges: List[Tuple[int, int]]) -> List[List[int]]:
        """
        Finds connected components induced by a set of edges.

        Args:
            n (int): Number of nodes.
            edges (List[Tuple[int, int]]): Active edges.

        Returns:
            List[List[int]]: List of connected components.
        """
        adj = [[] for _ in range(n)]
        for i, j in edges:
            adj[i].append(j)
            adj[j].append(i)

        visited = [False] * n
        components = []

        for v in range(n):
            if not visited[v]:
                comp = []
                dq = deque([v])
                visited[v] = True
                while dq:
                    u = dq.popleft()
                    comp.append(u)
                    for w in adj[u]:
                        if not visited[w]:
                            visited[w] = True
                            dq.append(w)
                components.append(comp)

        return components

    def _extract_path(self, n: int, edges: List[Tuple[int, int]], start: int) -> List[int]:
        """
        Reconstructs a Hamiltonian path starting from the fixed start node.

        Args:
            n (int): Number of nodes.
            edges (List[Tuple[int, int]]): Edges in the solution.
            start (int): Index of the start node.

        Returns:
            List[int]: Ordered list of node indices.
        """
        adj = [[] for _ in range(n)]
        for i, j in edges:
            adj[i].append(j)
            adj[j].append(i)

        path = [start]
        prev = -1
        cur = start

        while True:
            nxt = None
            for v in adj[cur]:
                if v != prev:
                    nxt = v
                    break
            if nxt is None:
                break
            path.append(nxt)
            prev, cur = cur, nxt

        return path
    
    def _subtour_elimination_callback(self, model: gp.Model, where: int) -> None:
        """
        Lazy constraint callback for subtour elimination.

        This callback prevents the formation of disconnected subtours
        that do not include the fixed start node.

        Args:
            model (gp.Model): Gurobi optimization model.
            where (int): Callback execution context.
        """
        if where == gp.GRB.Callback.MIPSOL:
            vals = {
                (i, j): model.cbGetSolution(var)
                for (i, j), var in model._xvars.items()
            }

            active_edges = [(i, j) for (i, j), v in vals.items() if v > 0.5]

            components = self._find_components(model._n, active_edges)
            for comp in components:
                if len(comp) == model._n:
                    continue
                if model._start in comp:
                    continue
                if len(comp) > 1:
                    expr = gp.quicksum(
                        model._xvars[(i, j)]
                        for i in comp for j in comp if i < j
                    )
                    model.cbLazy(expr <= len(comp) - 1)

    def _solve(self, points: List[Point2D], start_point: int) -> Dict:
        """
        Solves the eSHP problem with a fixed start point.

        Args:
            points (List[Point2D]): List of 2D points.
            start_point (int): Index of the fixed start point.

        Returns:
            Dict: Solution dictionary containing status, objective value
                  and ordered points.
        """
        n = len(points)
        nodes = list(range(n))

        dist = {
            (i, j): self.euclidean_distance(points[i], points[j])
            for i in range(n) for j in range(i + 1, n)
        }

        m = gp.Model("eSHP")
        m.Params.LazyConstraints = 1
        m.Params.PreCrush = 1

        x = {
            (i, j): m.addVar(vtype=gp.GRB.BINARY, obj=d, name=f"x_{i}_{j}")
            for (i, j), d in dist.items()
        }
        m.update()

        for i in nodes:
            deg_expr = gp.quicksum(
                x[(min(i, j), max(i, j))]
                for j in nodes if j != i
            )
            if i == start_point:
                m.addConstr(deg_expr == 1)
            else:
                m.addConstr(deg_expr <= 2)

        m.addConstr(gp.quicksum(x.values()) == n - 1)
        m.modelSense = gp.GRB.MINIMIZE

        m._xvars = x
        m._n = n
        m._start = start_point

        m.optimize(self._subtour_elimination_callback)

        sol_edges = [(i, j) for (i, j), var in x.items() if var.x > 0.5]
        path = self._extract_path(n, sol_edges, start_point)

        return {
            "status": m.status,
            "obj": m.objVal if m.status == gp.GRB.OPTIMAL else None,
            "ordered_points": [points[i] for i in path]
        }

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------
    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        Plans a path using the eSHP solver.

        Args:
            start_point (Point2D): Starting point.
            points (List[Point2D]): Points to visit.

        Returns:
            List[Point2D]: Ordered path.
        """
        if not points:
            return []
        
        all_points = [start_point] + points
        result = self._solve(all_points, start_point=0)
        return result["ordered_points"][1:] if result["ordered_points"] else []
