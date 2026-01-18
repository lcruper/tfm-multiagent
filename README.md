# Multi-agent system for autonomous exploration using a drone and a robot dog

This repository implements a **collaborative heterogeneous multi-agent system** combining an **aerial explorer (drone)** and a **ground inspector (robot dog)**. 

High-level control is implemented in **Python 3.14.2**, with embedded firmware for the drone and camera modules.

---

## Overview

The system performs **autonomous exploration and inspection** of unknown environments. It focuses on **detecting, localizing, and inspecting points of interest** efficiently.

The system operates in **missions**, each divided into two phases:

- **Exploration phase**: the drone surveys the assigned region and detects points of interest.
- **Inspection phase**: the robot dog receives the detected points, plans an efficient route, and executes inspection tasks at each location.

---

## Drone

**Role:** Exploration / Aerial agent  

**Hardware:**
- **Board:** ESP32-S2-Drone V1.2
- **Microcontroller:** ESP32-S2
- **Sensors:** IMU
- **Power:** LiPo battery 3.7 V 300 mAh
- **Communication:** Wi-Fi Access Point
- **Camera Module:**
  - **Board:** ESP32-CAM
  - **Sensor:** OV2640
  - **Communication:** Wi-Fi

**Firmware:**
- **Drone (ESP32-S2):**
  - **Framework:** ESP-IDF v4.4
  - **Base project:** ESP-Drone (located in `esp-drone/` folder)  
    Original project: [https://github.com/espressif/esp-drone](https://github.com/espressif/esp-drone)
- **Camera (ESP32-CAM):**
  - **Framework:** Arduino
  - **Base project:** CameraWebServer example (located in `CameraWebServer/` folder)  
    Original project: [https://github.com/espressif/esp32-camera](https://github.com/espressif/esp32-camera)

---

## Robot Dog

**Role:** Inspection / Ground agent (simulated)  
**Hardware:** N/A (simulated)  
**Software / Firmware:** Implemented in Python (`MultiagentSystem/src/robotDod/robot_dog_simulator.py`)

---

## Project Structure

The repository is organized as follows:

```
tfm-multiagent/
├── CameraWebServer/ # Camera firmware (ESP32-CAM, Arduino)
├── esp-drone/ # Drone firmware (ESP32-S2, ESP-IDF)
├── MultiagentSystem 
|   ├── docs/ # Sphinx source files for documentation
|   ├── input/ # Input data files
|   ├── src/ # Python source code for the system
|   ├── requirements.txt # Python dependencies
├── diagrams/ # UML and architecture diagrams
└── README.md # This file
```

---

## Requirements

**Software:**
- **Python 3.14** or higher
- Python **dependencies** `MultiagentSystem/requirements.txt`
- Optional: **Gurobi Optimizer** (required only for exact route planning algorithms)

**Hardware (optional):**
- **Drone:**
  - Platform: **ESP32-S2-Drone V1.2** 
  - Framework to build and flash firmware: **ESP-IDF v4.4**

- **Camera Module:**
  - Platform: **ESP32-CAM**
  - Framework to build and flash firmware: **Arduino IDE**
    
> Note: All functionality can be tested using simulated agents without the physical hardware.

---

## Installation

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install Python dependencies.
4. Optional: Hardware setup (if available):
   1. Flash firmware to the drone (`esp-drone/`) using ESP-IDF v4.4.
   2. Update camera code (`CameraWebServer/`) with the IP and password of the drone's Wi-Fi AP.
   3. Flash firmware to the camera using Arduino IDE.
   4. Connect the PC to the drone's Wi-Fi AP.
6. Configure parameters: edit the configuration files in `MultiagentSystem/src/configuration/` to set:
     - Input file path of the operation to execute
      - Camera IP address (if using hardware)
7. Run the system `python MultiagentSystem/src/main.py`


