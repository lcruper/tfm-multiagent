
from typing import List
from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner

class NearestNeighborPlanner(IPathPlanner):
    """
    Nearest Neighbor path planner.

    This planner builds a path starting from a fixed start point and
    repeatedly selects the closest unvisited point.
    """
    
    # ----------------------------------------------------------------
    # Private Methods
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Public Methods
    # ----------------------------------------------------------------

    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        Computes an ordered path using the Nearest Neighbor heuristic.

        The algorithm starts at the given start point and repeatedly selects
        the closest point from the set of remaining unvisited points. Each
        selected point is appended to the path. The process ends when no points remain.

        Args:
            start_point (Point2D): Initial position from which the path is built.
            points (List[Point2D]): Set of target points to be visited.

        Returns:
            List[Point2D]: Ordered list of points representing the visiting
            sequence computed by the heuristic. If the input list is empty,
            an empty list is returned.
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

