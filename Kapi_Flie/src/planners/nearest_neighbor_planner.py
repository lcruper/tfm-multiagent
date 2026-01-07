"""
Nearest Neighbor Planner Module
-------------------------------

Path planner based on the Nearest Neighbor heuristic.

This module implements a simple greedy algorithm that constructs a path
by iteratively visiting the closest unvisited point.
"""

from typing import List

from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner


class NearestNeighborPlanner(IPathPlanner):
    """
    Nearest Neighbor path planner.

    This planner builds a path starting from a fixed start point and
    repeatedly selects the closest unvisited point until all points
    have been visited.
    """

    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        Plans a path using the Nearest Neighbor heuristic.

        Args:
            start_point (Point2D): Starting (x, y) coordinates.
            points (List[Point2D]): List of points to visit.

        Returns:
            List[Point2D]: Ordered list of points representing the planned path.
        """
        if not points:
            return []

        current = start_point
        remaining = points.copy()
        path: List[Point2D] = []

        while remaining:
            next_point = min(remaining, key=lambda p: self._euclidean_distance(current, p))
            path.append(next_point)
            remaining.remove(next_point)
            current = next_point

        return path


    def _euclidean_distance(self, p1: Point2D, p2: Point2D) -> float:
        """
        Computes the Euclidean distance between two points.

        Args:
            p1 (Point2D): First point.
            p2 (Point2D): Second point.

        Returns:
            float: Euclidean distance between p1 and p2.
        """
        return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5