import gurobipy as gp
from typing import List, Tuple, Dict

from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner

class ILPPlanner(IPathPlanner):
    """
    Exact path planner.
    
    This class implements an optimization-based path planning strategy based on
    an Integer Linear Programming (ILP) formulation of the routing problem. 
    The objective is to minimize the
    total traveled Euclidean distance while visiting each point exactly once.
    
    The ILP model is solved using the commercial solver Gurobi through its Python
    API (``gurobipy``).
    """

    # ---------------------------------------------------
    # Private methods
    # ---------------------------------------------------
    def _extract_path(self, edges: List[Tuple[int, int]]) -> List[int]:
        """
        Reconstructs an ordered path from the selected edges of the solution.

        Args:
            edges (List[Tuple[int, int]]): Edges selected in the solution.

        Returns:
            List[int]: Ordered list of point indices representing the path.
        """
        adj = [[] for _ in range(len(edges) + 1)]
        for i, j in edges:
            adj[i].append(j)
            adj[j].append(i)

        path = [0]
        prev = -1
        cur = 0

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

    def _solve_gurobi(self, points: List[Point2D]) -> Dict:
        """
        Builds and solves the ILP model for the path planning problem.

        This method formulates the routing problem as an integer linear program
        where binary variables indicate whether an edge between two points is
        selected.

        Args:
            points (List[Point2D]): List of all points, including the starting point in index 0.

        Returns:
            Dict: Dictionary containing:
                - status: Solver termination status.
                - obj: Objective value (total distance), if optimal.
                - ordered_points: List of points in visiting order.
        """    
        n = len(points)
        nodes = list(range(n))

        dist = {
            (i, j): self._euclidean_distance(points[i], points[j])
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
            if i == 0:
                m.addConstr(deg_expr == 1)
            else:
                m.addConstr(deg_expr <= 2)

        m.addConstr(gp.quicksum(x.values()) == n - 1, name ="total_edges")

        m.modelSense = gp.GRB.MINIMIZE
        m.optimize()

        sol_edges = [(i, j) for (i, j), var in x.items() if var.x > 0.5]
        path = self._extract_path(sol_edges)

        return {
            "status": m.status,
            "obj": m.objVal if m.status == gp.GRB.OPTIMAL else None,
            "ordered_points": [points[i] for i in path]
        }

    def _euclidean_distance(self, p1: Point2D, p2: Point2D) -> float:
        """
        Computes the Euclidean distance between two 2D points.

        Args:
            p1 (Point2D): First point.
            p2 (Point2D): Second point.

        Returns:
            float: Euclidean distance between the two points.
        """
        return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    
    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------
    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        Computes an optimal visiting order for a set of target points.

        The path always starts from the provided start point. The start point
        itself is not included in the returned list.

        Args:
            start_point (Point2D): Starting point of the path.
            points (List[Point2D]): Target points to be visited.

        Returns:
            List[Point2D]: Ordered list of points representing the planned path.
        """
        if not points:
            return []
        
        all_points = [start_point] + points
        result = self._solve_gurobi(all_points)
        return result["ordered_points"][1:] if result["ordered_points"] else []
