"""
ILP Planner Module
------------------

Integer Linear Programming (ILP) solver with fixed start point.

This module implements an optimization-based path planner using Gurobi,
solving the Integer Linear Programming formulation.
"""

import gurobipy as gp
from typing import List, Tuple, Dict

from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner


class ILPPlanner(IPathPlanner):
    """
    Integer Linear Programming formulation solver with fixed start point.

    This planner computes the minimum-length path that:
    - starts from a fixed start point
    - visits all remaining points exactly once
    - minimizes the total Euclidean distance

    The problem is solved using Gurobi.
    """

    # ---------------------------------------------------
    # Internal methods
    # ---------------------------------------------------
    def _extract_path(self, n: int, edges: List[Tuple[int, int]], start: int) -> List[int]:
        """
        Reconstructs path starting from the fixed start node.

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

    def _solve(self, points: List[Point2D], start_point: int) -> Dict:
        """
        Solves the ILP formulation.

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

        m = gp.Model()

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

        m.modelSense = gp.GRB.MINIMIZE

        m._xvars = x
        m._n = n
        m._start = start_point
        
        m.optimize()

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
