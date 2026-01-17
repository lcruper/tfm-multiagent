Operation Package
=================

This package contains the modules related to the management of the overall operation of the multi-agent system.
Its main purpose is to coordinate, concurrently and synchronously, the execution of exploration and inspection phases across the different missions that compose a complete operation. 

The package provides the necessary mechanisms for managing and tracking the state of the operation and the mission's phases, 
synchronizing the agents through events, controlling the explorer and inspector agents, coordinating the operation flow, and visualizing the operation's progress in real-time.

.. toctree::
   :maxdepth: 1

   operation_status
   operation_events
   explorer_worker
   inspector_worker
   operation_controller
   operation_visualizer