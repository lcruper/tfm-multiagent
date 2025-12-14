# nearest_neighbor_planner.py
"""
@file nearest_neighbor_planner.py
@brief Implementation of a path planner using the Nearest Neighbor heuristic.
"""
from structures.structures import Point2D   
from interfaces.interfaces import IPathPlanner
from typing import List, Tuple
class NearestNeighborPlanner(IPathPlanner):
    """
    @brief Orders points using the Nearest Neighbor heuristic.
    @details Given a list of points, this planner constructs a path by repeatedly visiting the nearest unvisited point until all points have been visited.
    """

    def plan_path(self, start_point: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        @brief Plans a path using the Nearest Neighbor heuristic.

        @param start_point The starting (x, y) coordinates.
        @param points List of (x, y) coordinates to visit.
        @return Ordered list of (x, y) coordinates representing the planned path.
        """
        if not points:
            return []
        
        current = start_point

        remaining = points.copy()
        path = []

        while remaining:
            next_point = min(remaining, key=lambda p: self.euclidean_distance(current, p))
            path.append(next_point)
            remaining.remove(next_point)
            current = next_point

        return path
