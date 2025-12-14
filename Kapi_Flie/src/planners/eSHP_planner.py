# eSHP_planner.py
"""
@file eSHP_planner.py
@brief Euclidean Shortest Hamiltonian Path solver with fixed start point
       using Gurobi and lazy subtour elimination.
"""
import gurobipy as gp
from gurobipy import GRB
from collections import deque
from typing import List, Tuple, Dict

from structures.structures import Point2D

from interfaces.interfaces import IPathPlanner


class eSHPPlanner(IPathPlanner):
    """
    @class eSHPPlanner
    @brief Solver for the Euclidean Shortest Hamiltonian Path (eSHP)
           with a fixed start point.

    This solver computes the minimum-length Hamiltonian path that
    starts at a specified point and visits all other points exactly once.
    """

    def _find_components(self,
                         n: int,
                         edges: List[Tuple[int, int]]) -> List[List[int]]:
        """
        @brief Find connected components induced by a set of edges

        @param n Number of nodes
        @param edges List of undirected edges (i, j)
        @return List of connected components
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

    def _extract_path_from_start(self,
                                 n: int,
                                 edges: List[Tuple[int, int]],
                                 start: int) -> List[int]:
        """
        @brief Reconstruct a Hamiltonian path starting from the fixed start node

        @param n Number of nodes
        @param edges List of undirected edges (i, j)
        @param start Fixed start node index
        @return Ordered list of node indices in visiting order
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

    def _subtour_elimination_callback(self,
                                     model: gp.Model,
                                     where: int) -> None:
        """
        @brief Lazy constraint callback for subtour elimination

        @param model Gurobi model
        @param where Callback context
        """
        if where == GRB.Callback.MIPSOL:
            vals = {
                (i, j): model.cbGetSolution(var)
                for (i, j), var in model._xvars.items()
            }

            active_edges = [
                (i, j) for (i, j), v in vals.items() if v > 0.5
            ]

            components = self._find_components(model._n, active_edges)
            for comp in components:
                # Skip full component
                if len(comp) == model._n:
                    continue

                # Do not cut the component containing the start node
                if model._start in comp:
                    continue

                if len(comp) > 1:
                    expr = gp.quicksum(
                        model._xvars[(i, j)]
                        for i in comp for j in comp if i < j
                    )
                    model.cbLazy(expr <= len(comp) - 1)

    def _solve(self,
              points: List[Point2D],
              start_point: int) -> Dict:
        """
        @brief Solve the Euclidean Shortest Hamiltonian Path problem
               with a fixed start point.

        @param points List of 2D points (x, y)
        @param start_point Index of the fixed start point (0-based)
        @return Dictionary containing the solution
        """
        n = len(points)
        nodes = list(range(n))

        # Compute distances
        dist = {
            (i, j): self.euclidean_distance(points[i], points[j])
            for i in range(n) for j in range(i + 1, n)
        }

        # Build model
        m = gp.Model("eSHP")
        m.Params.LazyConstraints = 1
        m.Params.PreCrush = 1

        # Decision variables
        x = {
            (i, j): m.addVar(
                vtype=GRB.BINARY,
                obj=d,
                name=f"x_{i}_{j}"
            )
            for (i, j), d in dist.items()
        }
        m.update()

        # Degree constraints
        for i in nodes:
            deg_expr = gp.quicksum(
                x[(min(i, j), max(i, j))]
                for j in nodes if j != i
            )

            if i == start_point:
                m.addConstr(deg_expr == 1, name="deg_start")
            else:
                m.addConstr(deg_expr <= 2, name=f"deg_{i}")

        # Path has exactly n - 1 edges
        m.addConstr(
            gp.quicksum(x.values()) == n - 1,
            name="num_edges"
        )

        m.modelSense = GRB.MINIMIZE

        # Store data for callback
        m._xvars = x
        m._n = n
        m._start = start_point

        # Optimize
        m.optimize(self._subtour_elimination_callback)

        # Extract solution
        sol_edges = [
            (i, j) for (i, j), var in x.items() if var.x > 0.5
        ]

        path = self._extract_path_from_start(n, sol_edges, start_point)
        ordered_points = [points[i] for i in path]

        return {
            "status": m.status,
            "obj": m.objVal if m.status == GRB.OPTIMAL else None,
            "ordered_points": ordered_points
        }
    
    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        @brief Plans a path using the eSHP solver.

        @param start_point The starting (x, y) coordinates.
        @param points List of (x, y) coordinates to visit.
        @return Ordered list of (x, y) coordinates representing the planned path.
        """
        all_points = [start_point] + points
        result = self._solve(all_points, start_point=0)
        return result["ordered_points"][1:] if result["ordered_points"] else []
