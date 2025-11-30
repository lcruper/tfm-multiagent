#pragma once

#include <stdint.h>

/**
 * @brief Starts the battery monitoring task.
 */
void startBatteryMonitor(void);

/**
 * @brief Starts the position and orientation monitoring task.
 */
void startPositionMonitor(void);

/**
 * @brief Starts all monitoring tasks (battery + position).
 */
void startTelemetry(void);
