Nearest Neighbor Planner
========================

This module implements a heuristic path planner based on the nearest neighbor
strategy.

Starting from a given initial position, the planner iteratively selects the
closest unvisited point and appends it to the path. The process continues until
all target points have been visited. Although this approach does not guarantee
an optimal solution, it provides a fast and simple method for generating
reasonable paths with low computational cost.


.. automodule:: planners.nearest_neighbor_planner
   :members:
   :undoc-members:
   :show-inheritance:
