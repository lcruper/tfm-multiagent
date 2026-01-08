Drone Package
=============

This package contains the modules related to the explorer agent of the system.
The explorer agent is a drone equipped with a camera and is responsible
for carrying out the inspection phase.

During exploration, the agent captures images of the environment, 
associated with some telemetry data, and performs visual detection of points of interest. 
These points are later passed to the inspector agent for detailed inspection.

.. toctree::
   :maxdepth: 1

   drone_telemetry
   spiral_movement_simulator
   camera_capture
   camera_simulator
   matcher
   color_detection
   viewer
   drone